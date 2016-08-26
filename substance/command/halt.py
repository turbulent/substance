from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Halt(Command):

  def getUsage(self):
    return "substance suspend"
   
  def getHelpTitle(self):
    return "Suspend the current engine's virtual machine"

  def getShellOptions(self, optparser):
    optparser.add_option("-f", "--force", dest="force", help="Force power off", action="store_true")
    return optparser

  def main(self):

    forced = self.getOption('force')
    if forced and  not Shell.printConfirm("You are about to force halt the engine."):
      self.exitOK("User cancelled.")

    return self.core.readCurrentEngineName() \
      .bind(self.core.loadEngine) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.stop, force=forced) \
      .catch(self.exitError)
