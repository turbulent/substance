import os
from substance.monads import *
from substance.constants import *
from substance.utils import readDotEnv, writeToFile
from substance import Shell
from substance.subenv import (SPECDIR, ENVFILE)
import jinja2

class SubenvSpec(object):
  def __init__(self, specPath, basePath, name=None, vars={}):
    self.specPath = specPath
    self.basePath = basePath
    self.envPath = None
    self.name = name
    self.envFiles = []
    self.overrides = vars
    self.vars = {}

  @staticmethod
  def fromPath(path, vars={}):
    if not os.path.isdir(path):
      return Fail(InvalidOptionError("Specified path '%s' does not exist." % path))

    if os.path.basename(path) == SPECDIR or not os.path.isdir(os.path.join(path, SPECDIR)):
      return Fail(InvalidOptionError("Invalid path specified. Please pass a path to a folder with a %s directory." % SPECDIR))
    specPath = os.path.join(path, SPECDIR)

    return SubenvSpec(specPath, path, os.path.basename(path), vars).scan()

  def scan(self):
    return self.loadEnvVars(self.overrides) \
      .then(self.loadEnvStruct)

  def applyTo(self, envPath):
    self.envPath = envPath
    return self.applyDirs() \
      .then(self.applyFiles)  \
      .then(self.writeEnv) \
      .then(lambda: OK(self))

  def writeEnv(self):
    dotenv = os.path.join(self.envPath, ENVFILE)
    logging.debug("Writing environment to: %s" % dotenv)
    env = "\n".join([ "%s=\"%s\"" % (k,v) for k,v in self.vars.iteritems() ])
    return Try.attempt(writeToFile, dotenv, env)
  
  def applyDirs(self):
    dirs = [self.envPath]
    dirs.extend([os.path.join(self.envPath, dir) for dir in self.struct['dirs']])
    map(lambda x: logging.debug("Creating directory '%s'"%x), dirs)
    return OK(dirs).mapM(Shell.makeDirectory)

  def applyFiles(self):
    ops = []
    for file in self.struct['files']:
      fname, ext = os.path.splitext(file)
      source = os.path.join(self.specPath, file)
      dest = os.path.join(self.envPath, file)

      if fname == ENVFILE:
        continue
      elif ext == '.jinja':
        logging.debug("Rendering '%s' to %s" % (file, dest))
        dest = os.path.splitext(dest)[0]
        ops.append(self.renderFile(file, dest, self.vars))
      else:
        logging.debug("Copying '%s' to %s" % (file, dest))
        ops.append(Shell.copyFile(os.path.join(self.specPath, file), os.path.join(self.envPath, file)))
      
    return Try.sequence(ops)
 
  def renderFile(self, source, dest, vars={}):
    try:
      tplEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(self.specPath))
      tpl = tplEnv.get_template(source)
 
      tplVars = vars.copy()
      tplVars.update({'subenv':self})

      logging.debug("%s" %tplVars)
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
      struct['dirs'].extend(dirs)
      struct['files'].extend(files)
    return OK(struct)
       
  def setEnvStruct(self, struct):
    self.struct = struct
    return OK(self)
 
  def setEnvVars(self, e={}):
    self.vars = e
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

    map(lambda x: logging.info("Loading dotenv file: '%s'" % x), self.envFiles)
    return Try.sequence(map(Try.attemptDeferred(readDotEnv), self.envFiles))  \
      .map(lambda envs: reduce(lambda acc,x: dict(acc, **x), envs))

  def __repr__(self):
    return "SubEnvSpec(%(name)s) spec:%(specPath)s base:%(basePath)s envFile:%(envFiles)s vars:%(vars)s files:%(struct)s" % self.__dict__
