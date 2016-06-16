import os
from substance.monads import *
from substance.constants import *
from substance.utils import readDotEnv, writeToFile
from substance import Shell
import jinja2

class SubenvAPI(object):
  '''
    Subenv API
  '''
  SPECDIR = '.subenv'
  ENVFILE = '.env'

  def __init__(self, basePath="/substance", devroot="/substance/devroot"):
    self.basePath = basePath
    self.envsPath = os.path.join(self.basePath, "envs")
    self.devroot = devroot
    self.assumeYes = False
    self.struct = {'dirs':[], 'files':[]}

  def setAssumeYes(self, b):
    if b:
      self.assumeYes = True
    else:
      self.assumeYes = False

  def initialize(self):
    return self.assertPaths()

  def assertPaths(self):
    return OK([self.basePath, self.envsPath, self.devroot]).mapM(Shell.makeDirectory)

  def init(self, path, env={}):
    logging.info("Initializing subenv from: %s" % path)
    return self._scanEnv(path, env) \
      .bind(self.l) \
      .bind(self._applyEnv)

  def l(self, e):
    logging.debug("%s" % e)
    return OK(e)

  def _applyEnv(self, envSpec):
    ''' pass '''
    envPath = os.path.join(self.envsPath, envSpec.name)
    return envSpec.applyTo(envPath)

  def _scanEnv(self, path, vars={}):
    if not os.path.isdir(path):
      return Fail(InvalidOptionError("Specified path '%s' does not exist." % path))

    if os.path.basename(path) == SubenvAPI.SPECDIR or not os.path.isdir(os.path.join(path, SubenvAPI.SPECDIR)):
      return Fail(InvalidOptionError("Invalid path specified. Please pass a path to a folder with a %s directory." % SubenvAPI.SPECDIR))
    specPath = os.path.join(path, SubenvAPI.SPECDIR)

    return SubEnvSpec(specPath, path, os.path.basename(path), vars).scan()

  def _loadEnvVars(self, envSpec, env={}):
    op = OK(env)
    if envSpec.envFile:
      op = self._readDotEnv(envSpec.envFile) 
    return op.map(lambda e: e.update(env))

     
class SubEnvSpec(object):
  def __init__(self, specPath, basePath, name=None, vars={}):
    self.specPath = specPath
    self.basePath = basePath
    self.envPath = None
    self.name = name
    self.envFiles = []
    self.overrides = vars
    self.vars = {}

  def scan(self):
    return self.loadEnvVars(self.overrides) \
      .then(self.loadEnvStruct)

  def applyTo(self, envPath):
    self.envPath = envPath
    return self.applyDirs() \
      .then(self.applyFiles) 

  def applyDirs(self):
    dirs = [self.envPath]
    dirs.extend([os.path.join(self.envPath, dir) for dir in self.struct['dirs']])
    return OK(dirs).mapM(Shell.makeDirectory)

  def applyFiles(self):
    ops = []
    for file in self.struct['files']:
      fname, ext = os.path.splitext(file)
      source = os.path.join(self.specPath, file)
      dest = os.path.join(self.envPath, file)

      if fname == SubenvAPI.ENVFILE:
        continue
      elif ext == '.jinja':
        dest = os.path.splitext(dest)[0]
        ops.append(self.renderFile(file, dest, self.vars))
      else:
        ops.append(Shell.copyFile(os.path.join(self.specPath, file), os.path.join(self.envPath, file)))
      
    return Try.sequence(ops)
 
  def renderFile(self, source, dest, vars={}):
    try:
      tplEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(self.specPath))
      tpl = tplEnv.get_template(source)
      with open(dest, 'wb') as fh:
        fh.write(tpl.render(**vars))
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
    specEnvFile = os.path.join(self.specPath, SubenvAPI.ENVFILE)
    if os.path.isfile(specEnvFile):
      self.envFiles.append(specEnvFile)

    baseEnvFile = os.path.join(self.basePath, SubenvAPI.ENVFILE)
    if os.path.isfile(baseEnvFile):
      self.envFiles.append(baseEnvFile)

    return Try.sequence(map(Try.attemptDeferred(readDotEnv), self.envFiles))  \
      .map(lambda envs: reduce(lambda acc,x: dict(acc, **x), envs))

  def __repr__(self):
    return "SubEnvSpec(%(name)s) spec:%(specPath)s base:%(basePath)s envFile:%(envFiles)s vars:%(vars)s files:%(struct)s" % self.__dict__
