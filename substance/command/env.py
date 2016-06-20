from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Env(Command):

  def getUsage(self):
    return "substance env [ENGINE NAME]"
 
  def getHelpTitle(self):
    return "Print the shell envvars required to connect to this engine's docker daemon"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.outputDockerEnv) \
      .catch(self.exitError)

  def outputDockerEnv(self, engine):
    publicIP = engine.getPublicIP()
    port = engine.getDockerPort()
    print("export DOCKER_API_VERSION=\"1.19\"")   
    print("export DOCKER_HOST=\"%s\"" % (engine.getDockerURL()))
    print("export DOCKER_TLS_VERIFY=\"\"")
    return OK(None)
