from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from substance.exceptions import (SubstanceError)

class Suspend(Command):
  def getUsage(self):
    return "substance suspend [ENGINE NAME]"
 
  def getHelpTitle(self):
    return "Suspend an engine gracefully."

  def main(self):
    name = self.getInputName()

    self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.suspend) \
      .catch(self.exitError)
