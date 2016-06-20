from substance.monads import *
from substance.exceptions import (SubstanceError)
from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance.subenv import (SubenvCommand, SPECDIR, SubenvAPI)


class Help(SubenvCommand):

  def getUsage(self):
    return "subenv help [COMMAND?]"

  def getHelpTitle(self):
    return "Obtain help on a subenv command"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    if len(self.args) > 0:
      command = self.args[0]
      package = 'substance.subenv.command'
      className = None
    else:
      command = 'cli'
      package = 'substance.subenv'
      className = 'SubenvCLI'

    commandClass = self.findCommandClass(command, package, className)
    cmd = commandClass()
    return cmd.exitHelp()

  def getInputCommand(self):
    name = self.args[0]
    return name

