from builtins import map
from builtins import object
import os
import time
from collections import OrderedDict
from substance.monads import *
from substance.constants import *
from substance.utils import readDotEnv, writeToFile, makeSymlink
from substance.exceptions import (InvalidEnvError, InvalidOptionError)
from substance.config import (Config)
from substance import Shell
from substance.subenv import (SPECDIR, ENVFILE, CODELINK, CONFFILE)
import jinja2
from functools import reduce

logger = logging.getLogger(__name__)

class SubenvSpec(object):
  def __init__(self, specPath, basePath, name=None, vars={}, lastApplied=None):
    self.specPath = specPath
    self.basePath = basePath
    self.envPath = None
    self.name = name
    self.envFiles = []
    self.overrides = vars
    self.vars = OrderedDict()
    self.lastApplied = lastApplied
    self.current = False
    self.struct = {'files': [], 'dirs': []}

  def setEnvPath(self, path):
    self.envPath = path
    self.config = Config(os.path.join(self.envPath, CONFFILE))
  
  @staticmethod
  def fromEnvPath(path):
    if not os.path.isdir(path):
      return Fail(InvalidOptionError("Specified path '%s' does not exist." % path))

    envPath = path
    name = os.path.basename(envPath)

    envVars = Try.attempt(readDotEnv, os.path.join(envPath, ENVFILE))
    if envVars.isFail():
      return envVars
    envVars = envVars.getOK()

    reserved = ['SUBENV_NAME','SUBENV_LASTAPPLIED','SUBENV_ENVPATH','SUBENV_SPECPATH','SUBENV_BASEPATH'] 
    vars = envVars.copy()
    for k in list(vars.keys()):
      if k in reserved:
        del vars[k]

    lastApplied = None   
    if 'SUBENV_LASTAPPLIED' in envVars:
      lastApplied = envVars['SUBENV_LASTAPPLIED']
   
    env = SubenvSpec(envVars['SUBENV_SPECPATH'], envVars['SUBENV_BASEPATH'], envVars['SUBENV_NAME'], vars, lastApplied)
    env.setEnvPath(envPath)
    return env

    
  @staticmethod
  def fromSpecPath(path, vars={}):
    if not os.path.isdir(path):
      return Fail(InvalidEnvError("Specified path '%s' does not exist." % path))

    if os.path.basename(path) == SPECDIR or not os.path.isdir(os.path.join(path, SPECDIR)):
      return Fail(InvalidOptionError("Invalid path specified. Please pass a path to a folder with a %s directory." % SPECDIR))
    specPath = os.path.join(path, SPECDIR)

    name = os.path.basename(path)

    return SubenvSpec(specPath, path, name, vars).scan()

  def getLastAppliedDateTime(self, fmt='%Y-%m-%d %H:%M:%S'):
    if self.lastApplied:
      return time.strftime(fmt, time.localtime(float(self.lastApplied)))
    return None
 
  def scan(self):
    return self.loadEnvVars(self.overrides) \
      .then(self.loadEnvStruct)

  def applyTo(self, envPath):
    self.setEnvPath(envPath)
    return self.clearEnv() \
      .then(self.applyDirs) \
      .then(self.applyFiles)  \
      .then(self.writeEnv) \
      .then(self.linkCode) \
      .then(self.assertConfig) \
      .then(self.applyScript) \
      .then(lambda: OK(self))

    
  def linkCode(self):
    return Try.sequence([
      Try.attempt(makeSymlink, self.basePath, os.path.join(self.envPath, CODELINK), True),
      Try.attempt(makeSymlink, self.specPath, os.path.join(self.envPath, SPECDIR), True)
    ])
  
  def clearEnv(self):
    if os.path.isfile(self.config.configFile):
      return Shell.rmFile(self.config.configFile)
    return OK(None)
   
  def writeEnv(self):
    dotenv = os.path.join(self.envPath, ENVFILE)
    logger.debug("Writing environment to: %s" % dotenv)
    envVars = OrderedDict(self.vars, **self.overrides)
    envVars.update({
      'SUBENV_NAME': self.name,
      'SUBENV_LASTAPPLIED': time.time(),
      'SUBENV_ENVPATH': self.envPath,
      'SUBENV_SPECPATH': self.specPath,
      'SUBENV_BASEPATH': self.basePath
    })

    env = "\n".join([ "%s=\"%s\"" % (k,v) for k,v in envVars.items() ])
    return Try.attempt(writeToFile, dotenv, env)
 
  def assertConfig(self):
    if not os.path.isfile(self.config.configFile):
      return OK({})
    return self.config.loadConfigFile() 

  def applyScript(self):
    commands = self.config.get('script', [])
    return Try.sequence(list(map(self.applyCommand,  commands)))

  def applyCommand(self, cmd):
    logger.info("Running environment command: %s" % cmd)
    return Shell.call(cmd, cwd=self.envPath, shell=True)

  def applyDirs(self):
    ops = [ Shell.makeDirectory(self.envPath, 0o750) ]
    for dir in self.struct['dirs']:
      sourceDir = os.path.join(self.specPath, dir)
      destDir = os.path.join(self.envPath, dir)
      mode = os.stat(sourceDir).st_mode & 0o777
      logger.debug("Creating directory '%s' mode: %s" % (dir, mode))
      ops.append(Shell.makeDirectory(destDir).bind(defer(Shell.chmod, mode=mode)))

    return Try.sequence(ops)

  def applyFiles(self):
    ops = []
    for file in self.struct['files']:
      fname, ext = os.path.splitext(file)
      source = os.path.join(self.specPath, file)
      dest = os.path.join(self.envPath, file)

      if fname == ENVFILE:
        continue
      elif ext == '.jinja':
        logger.debug("Rendering '%s' to %s" % (file, dest))
        dest = os.path.splitext(dest)[0]
        ops.append(self.renderFile(file, dest, self.vars))
      else:
        logger.debug("Copying '%s' to %s" % (file, dest))
        ops.append(Shell.copyFile(os.path.join(self.specPath, file), os.path.join(self.envPath, file)))
      
    return Try.sequence(ops)


  def getEnvVars(self):
    envVars = self.overrides.copy()
    envVars.update({
      'SUBENV_NAME': self.name,
      'SUBENV_LASTAPPLIED': self.lastApplied,
      'SUBENV_ENVPATH': self.envPath,
      'SUBENV_SPECPATH': self.specPath,
      'SUBENV_BASEPATH': self.basePath
    })
    return envVars
 
  def renderFile(self, source, dest, vars={}):
    try:
      tplEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(self.specPath))
      tpl = tplEnv.get_template(source)

      tplVars = self.getEnvVars() 
      tplVars.update({'subenv': self})
      tplVars.update({'SUBENV_VARS': self.getEnvVars()})
 
      with open(dest, 'wb') as fh:
        fh.write(tpl.render(**tplVars))
      return OK(None)
    except Exception as err:
      return Fail(err)
       
  def loadEnvStruct(self):
    return self.scanEnvStruct().bind(self.setEnvStruct) 

  def scanEnvStruct(self):
    struct = {'dirs':[], 'files':[]}
    for root, dirs, files in os.walk(self.specPath):
      relPath = os.path.relpath(root, self.specPath).strip('./').strip('/')
      for dir in dirs:
        struct['dirs'].append(os.path.join(relPath, dir))
      for file in files:
        struct['files'].append(os.path.join(relPath, file))
    return OK(struct)
       
  def setEnvStruct(self, struct):
    self.struct = struct
    return OK(self)
 
  def setEnvVars(self, e={}):
    self.overrides = e
    return OK(self)

  def loadEnvVars(self, env={}):
    return self.readEnvFiles() \
      .map(lambda e: dict(e, **env)) \
      .bind(self.setEnvVars)

  def readEnvFiles(self):
    specEnvFile = os.path.join(self.specPath, ENVFILE)
    if os.path.isfile(specEnvFile):
      self.envFiles.append(specEnvFile)

    baseEnvFile = os.path.join(self.basePath, ENVFILE)
    if os.path.isfile(baseEnvFile):
      self.envFiles.append(baseEnvFile)

    list(map(lambda x: logger.info("Loading dotenv file: '%s'" % x), self.envFiles))
    return Try.sequence(list(map(Try.attemptDeferred(readDotEnv), self.envFiles)))  \
      .map(lambda envs: reduce(lambda acc,x: dict(acc, **x), envs, {}))

  def __repr__(self):
    return "SubEnvSpec(%(name)s) spec:%(specPath)s base:%(basePath)s envFile:%(envFiles)s vars:%(vars)s files:%(struct)s" % self.__dict__
