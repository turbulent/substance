from __future__ import absolute_import
import sys
import logging
from collections import OrderedDict
from substance import (Program, Core)
import substance.command

class SubstanceCLI(Program):
  """Substance CLI command"""

  def __init__(self):
    super(SubstanceCLI, self).__init__()

  def setupCommands(self):
    self.addCommand('engine', 'substance.command.engine')
    self.addCommand('use', 'substance.command.use')
    self.addCommand('switch', 'substance.command.switch')
    return self

  def getShellOptions(self, optparser):
    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelpTitle(self):
    return "Local docker-based development environments"

  def initCommand(self, command):
    core = Core()
    if self.getOption('assumeYes'):
      core.setAssumeYes(True)
    command.core = core
    return command

def cli():
  args = sys.argv
  args.pop(0)

  prog = SubstanceCLI()
  prog.execute(args)
