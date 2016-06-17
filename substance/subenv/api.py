import os
from substance.monads import *
from substance.constants import *
from substance import Shell
from substance.subenv import SubenvSpec

class SubenvAPI(object):
  '''
    Subenv API
  '''
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
    return SubenvSpec.fromPath(path, env) \
      .bind(self._applyEnv)

  def _applyEnv(self, envSpec):
    envPath = os.path.join(self.envsPath, envSpec.name)
    logging.info("Applying environment to: %s" % envPath)
    return envSpec.applyTo(envPath)

