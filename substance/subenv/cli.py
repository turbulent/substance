import sys
import logging
import traceback
from importlib import import_module
from optparse import OptionParser

from substance import (Command, Core)

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

    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")

    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelp(self):
    """Retrieve the help string for this command"""
    helpUsage = """
Usage: subenv COMMAND [options] [CONTAINERS..]

subenv - Initialize a substance dockerized environment.

Options:
  -f    Alternate config file location
  -d    Activate debugging logs
  -y    Assume yes when prompted

Commands:

  subenv ls
  subenv create PATH/TO/PROJECT
  subenv use PROJECT
  subenv delete PROJECT
 
Samples: 

  subenv create 
    -b /substance
    -d /substance/devroot
    -e envfile
    -D VAR=value
    -D VAR1=value
    -D VAR2=value
    -D VAR3=value
    -n project-name
    project-name
 
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
        core.setAssumeYes(True)

      moduleName = 'substance.subenv.command.' + self.cmdString
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

    self.input = parsed
    self.commandInput = extraArgs

    (self.options, self.args) = self.parseShellInput()
    self.main()



def cli():
  prog = SubenvCLI()
  prog.execute(sys.argv)
