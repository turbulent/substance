from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Suspend(Command):

  def getUsage(self):
    return "substance suspend"
   
  def getHelpTitle(self):
    return "Suspend the current engine's virtual machine"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    engine = self.parent.getOption('engine')
    if engine:
      engine = OK(engine)
    else:
      engine = self.core.readCurrentEngineName()

    return engine \
      .bind(self.core.loadEngine) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.suspend) \
      .catch(self.exitError)
