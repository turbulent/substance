from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Help(Command):

  def getUsage(self):
    return "substance help [command?]"
  
  def getHelpTitle(self):
    return "Print help for a specific substance command"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    if len(self.args) > 0:
      commandName = self.args[0]
      command = self.parent.getCommand(commandName)
      command.initialize()
    else:
      command = self.parent
    return command.exitHelp()

  def getInputCommand(self):
    name = self.args[0]
    return name
