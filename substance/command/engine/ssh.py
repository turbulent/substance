from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Ssh(Command):

  def getUsage(self):
    return "substance ssh [ENGINE NAME]"
  
  def getHelpTitle(self):
    return "Connect using SSH to the engine's virtual machine."

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.getInputName()

    self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.shell) \
      .catch(self.exitError)
