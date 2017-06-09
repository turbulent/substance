from __future__ import print_function
from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Env(Command):

  def getUsage(self):
    return "substance engine env [ENGINE NAME]"
 
  def getHelpTitle(self):
    return "Print the shell variables to set up the local docker client environment"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(self.outputDockerEnv) \
      .catch(self.exitError)

  def outputDockerEnv(self, engine):
    env = engine.getDockerEnv()
    for k, v in env.items():
      print("export %s=\"%s\"" % (k,v))
    return OK(None)
