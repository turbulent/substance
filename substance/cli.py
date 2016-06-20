from __future__ import absolute_import

import sys
import logging
import traceback
import pkgutil
from collections import OrderedDict
from substance import (Command, Core)
import substance.command

class SubstanceCLI(Command):
  """Substance CLI command"""

  def __init__(self):
    super(SubstanceCLI, self).__init__()
    self.cmdString = None
    self.commandInput = None
    self.command = None

  def setupLogging(self):
    log_level = logging.DEBUG if self.options.debug else logging.INFO
    logging.basicConfig(format='%(message)s', level=log_level)

  def setupEnv(self):
    """Setup the Environment """

  def getShellOptions(self, optparser):
    Command.getShellOptions(self, optparser)

    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")

    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelpTitle(self):
    return "Local docker-based development environments"

  def getHelpDetails(self):
    helpUsage = "Commands:\n\n"
    for name, command in self.getCommandModules().iteritems():
      helpUsage += "  %-20s%s\n" % (name, command.getHelpTitle())
    return helpUsage

  def main(self):

    self.setupLogging()
    self.setupEnv()

    if not len(self.args) > 0:
      self.exitError("Please provide a command.\n\nCheck 'substance help' for available commands.")

    self.cmdString = self.args[0]
    self.commandInput = self.args[1:]

    try:
      core = Core()

      if self.options.assumeYes:
        core.setAssumeYes(True)

      commandClass = self.findCommandClass(self.cmdString)
      self.command = commandClass(core=core)
      self.command.execute(self.commandInput)
    except Exception as err:
      logging.error(traceback.format_exc())
      self.exitError("Error running command %s: %s" % (self.cmdString, err), code=2)

  def execute(self, args=None):
    args.pop(0)
    self.input = args
    (self.options, self.args) = self.parseShellInput(False)
    self.main()


  def getCommandModules(self):
    package = substance.command
    names = []
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
      if modname != 'command':
        names.append(modname)
    names.sort()
    classes = map(lambda x: self.findCommandClass(x)(), names)
    mods = OrderedDict(zip(names, classes))
    return mods
  
def cli():
  prog = SubstanceCLI()
  prog.execute(sys.argv)
