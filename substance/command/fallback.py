from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Fallback(Command):

  def getUsage(self):
    return ""
  
  def getHelpTitle(self):
    return ""

  def getShellOptions(self, optparser):
    return optparser

  # Disable parsing for this command
  def execute(self, args=None):
    self.input = args
    self.args = args
   
    self.main()

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envExecAlias, alias=self.name, args=self.args) \
      .catch(self.onEngineException)
  
  def onEngineException(self, e):
    return self.exitError("Invalid command '%s' specified for '%s'.\n\nUse 'substance help' for available commands." % (self.name, 'substance'))
