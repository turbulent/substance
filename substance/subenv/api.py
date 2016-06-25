import os
from substance.monads import *
from substance.constants import *
from substance.logs import dinfo
from substance import Shell
from substance.subenv import SubenvSpec
from substance.utils import makeSymlink, readSymlink

logger = logging.getLogger(__name__)

class SubenvAPI(object):
  '''
    Subenv API
  '''
  def __init__(self, basePath="/substance"):
    self.basePath = basePath
    self.envsPath = os.path.join(self.basePath, "envs")
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
    return OK([self.basePath, self.envsPath]).mapM(Shell.makeDirectory)

  def init(self, path, env={}, name=None):
    logger.info("Initializing subenv from: %s" % path)
    return SubenvSpec.fromSpecPath(path, env, name) \
      .bind(self._applyEnv)

  def exists(self, name):
    if os.path.isdir(os.path.join(self.envsPath, name)):
      return OK(True)
    return OK(False)

  def delete(self, name):
    envPath = os.path.normpath(os.path.join(self.envsPath, name))
    if not os.path.isdir(envPath):
      return Fail(InvalidOptionError("Environment '%s' does not exist."))
    return Shell.nukeDirectory(envPath)

  def use(self, name):
    envPath = os.path.normpath(os.path.join(self.envsPath, name))
    if not os.path.isdir(envPath):
      return Fail(InvalidOptionError("Environment '%s' does not exist."))
   
    envSpec = SubenvSpec.fromEnvPath(envPath)
    current = os.path.join(self.basePath, "current")
  
    return Try.attempt(makeSymlink, envSpec.envPath, current, True) \
      .then(dinfo("Current substance environment now: '%s'" % envSpec.name))

  def current(self):
    return OK(self._getCurrentEnv())
  
  def run(self, cmd, envName=None):
    if not envName:
      envSpec = self._getCurrentEnv() 
      if not envSpec:
        return Fail(InvalidEnvError("No env is currently active."))
      envName = envSpec.name

    return OK(envName) \
      .bind(self._loadEnvSpec) \
      .map(lambda x: x.envPath) \
      .bind(lambda p: Shell.streamCommand(cmd, cwd=p, shell=True))

     
  def ls(self):
    envs = []
    current = self._getCurrentEnv()
    for f in os.listdir(self.envsPath):
      path = os.path.join(self.envsPath, f)
      if os.path.isdir(path):
        env = SubenvSpec.fromEnvPath(path)
        if current and env.envPath == current.envPath:
          env.current = True
        envs.append(env)
    return OK(envs)
   
  def _loadEnvSpec(self, name):
    envPath = os.path.normpath(os.path.join(self.envsPath, name))
    if not os.path.isdir(envPath):
      return Fail(InvalidOptionError("Environment '%s' does not exist."))
    return OK(SubenvSpec.fromEnvPath(envPath))

  def _getCurrentEnv(self):
    try:
      current = readSymlink(os.path.join(self.basePath, "current"))
      return SubenvSpec.fromEnvPath(current)
    except Exception as err:
      return None

  def _applyEnv(self, envSpec):
    envPath = os.path.join(self.envsPath, envSpec.name)
    logger.info("Applying environment to: %s" % envPath)
    return envSpec.applyTo(envPath)

