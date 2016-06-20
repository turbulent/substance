from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Help(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    if len(self.args) > 0:
      command = self.args[0]
      package = 'substance.command'
      className = None
    else:
      command = 'cli'
      package = 'substance'
      className = 'SubstanceCLI'

    commandClass = self.findCommandClass(command, package, className)
    cmd = commandClass()
    return cmd.exitHelp()

  def getInputCommand(self):
    name = self.args[0]
    return name

