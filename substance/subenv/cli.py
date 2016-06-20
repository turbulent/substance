import sys
import logging
import traceback
import pkgutil
from collections import OrderedDict
from importlib import import_module
from substance import (Command, Core)
from substance.subenv import SubenvAPI
import substance.subenv.command

class SubenvCLI(Command):
  """Subenv CLI command"""

  def __init__(self):
    super(SubenvCLI, self).__init__()
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

    optparser.add_option("-d", '--debug',  dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option('-y', "--yes", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")
    optparser.add_option('-b', '--base', type="str", dest="base", help="Path to the base", default="/substance")
    return optparser

  def getUsage(self):
    return "subenv [options] COMMAND [command-options]"

  def getHelpTitle(self):
    return "Initialize a substance project environment"

  def getHelpDetails(self):
    helpUsage = "Commands:\n\n"
    for name, command in self.getCommandModules().iteritems():
      helpUsage += "  %-20s%s\n" % (name, command.getHelpTitle())
    return helpUsage

  def main(self):

    self.setupLogging()
    self.setupEnv()

    if not len(self.args) > 0:
      self.exitError("Please provide a command.\n\nCheck 'subenv help' for available commands.")

    self.cmdString = self.args[0]
    self.commandInput = self.args[1:]

    try:
      core = Core()
      api = SubenvAPI(self.options.base)

      if self.options.assumeYes:
        core.setAssumeYes(True)

      commandClass = self.findCommandClass(self.cmdString, package='substance.subenv.command')
      self.command = commandClass(core=core, api=api)
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
    package = substance.subenv.command
    names = []
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
      if modname != 'command':
        names.append(modname)
    names.sort()
    classes = map(lambda x: self.findCommandClass(x, package='substance.subenv.command')(), names)
    mods = OrderedDict(zip(names, classes))
    return mods

def cli():
  prog = SubenvCLI()
  prog.execute(sys.argv)
