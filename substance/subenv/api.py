import os
from substance.monads import *
from substance.constants import *
from substance import Shell
from substance.subenv import SubenvSpec

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

  def init(self, path, env={}):
    logging.info("Initializing subenv from: %s" % path)
    return SubenvSpec.fromSpecPath(path, env) \
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
    
  def ls(self):
    envs = []
    for f in os.listdir(self.envsPath):
      path = os.path.join(self.envsPath, f)
      if os.path.isdir(path):
        envs.append(SubenvSpec.fromEnvPath(path))
    return OK(envs)
       
  def _applyEnv(self, envSpec):
    envPath = os.path.join(self.envsPath, envSpec.name)
    logging.info("Applying environment to: %s" % envPath)
    return envSpec.applyTo(envPath)

