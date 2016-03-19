import sys
import logging
import traceback
from importlib import import_module
from optparse import OptionParser
from substance.command import Command
from substance.core import Core

class Substance(Command):
  """Substance CLI command"""

  cmdString = None
  command = None
  input = None
  commandInput = None

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

  def getHelp(self):
    """Retrieve the help string for this command"""
    helpUsage = """
Usage: substance COMMAND [options] [CONTAINERS..]

substance - Local dockerized development environment.

Options:
  -f    Alternate config file location
  -d    Activate debugging logs

Commands:

  # Engine List, Init and Delete
  substance ls
  substance init mybox
  substance delete mybox

  # Engine Control
  substance launch mybox
  substance stop mybox
  substance deprovision mybox

  # Task Control
  substance task mybox load /projects/myproject/containers.yml
  substance task mybox status -a
  substance task mybox start -a
  substance task mybox stop -a
  substance task mybox remove -a
  substance task mybox recreate -a

  substance enter mybox myboxweb
  
  substance env mybox

  #Porcelain
  substance spawn -c client -p project 
  substance make mybox mytask
  substance watch mybox mytask
  substance test mybox mytask
  substance exec mybox mytask "make.sh"
 
  # Logs
  substance logs mybox taskname

"""
    return helpUsage

  def main(self):

    self.setupLogging()
    self.setupEnv()

    if not len(self.args) > 0:
      self.exitHelp("Please provide a command.")

    if self.getOption('help'):
      return self.exitHelp()

    self.cmdString = self.args[0]

    try:

      core = Core()

      if self.options.assumeYes:
        core.setConfigKey("assumeYes", True)

      moduleName = 'substance.command.'+self.cmdString
      className = self.cmdString.title()

      logging.debug("Import %s, ClassName: %s", moduleName, className)

      module_ = import_module(moduleName)
      class_ = getattr(module_, className)
      self.command = class_(core=core)
    except ImportError, err:
      logging.debug("%s", err)
      self.exitError("Unrecognized command %s" % self.cmdString)

    try:
      self.command.execute(self.commandInput)
    except Exception as err:
      logging.error(traceback.format_exc())
      self.exitError("Error running command %s: %s" % (self.cmdString, err), code=2)

  def execute(self, args=None):
    args.pop(0)

    parsed = []
    extraArgs = []
    i = 0
    for arg in args:
      if i >= 1:
        extraArgs.append(arg)
        continue

      if arg[0] == '-' or arg[0:2] == '--':
        parsed.append(arg)
      else:
        parsed.append(arg)
        i += 1

    #print("Top Level Input: %s" % parsed)
    #print("Command Input: %s" % extraArgs)

    self.input = parsed
    self.commandInput = extraArgs

    (self.options, self.args) = self.parseShellInput()
    self.main()

