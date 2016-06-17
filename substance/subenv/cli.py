import sys
import logging
import traceback
from importlib import import_module
from optparse import OptionParser

from substance import (Command, Core)
from substance.subenv import SubenvAPI

class SubenvCLI(Command):
  """Subenv CLI command"""

  def __init__(self):
    super(SubenvCLI, self).__init__()
    self.cmdString = None
    self.commandInput = None
    self.command = None
    self.commands = ['init','delete','ls']

  def setupLogging(self):
    log_level = logging.DEBUG if self.options.debug else logging.INFO
    logging.basicConfig(format='%(message)s', level=log_level)

  def setupEnv(self):
    """Setup the Environment """

  def getShellOptions(self, optparser):
    Command.getShellOptions(self, optparser)

    optparser.add_option("-d", '--debug',  dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option('--yes', "-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")
    optparser.add_option('-b', '--base', type="str", dest="base", help="Path to the base", default="/substance")
    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelp(self):
    """Retrieve the help string for this command"""
    helpUsage = """
Usage: subenv COMMAND [options] [CONTAINERS..]

subenv - Initialize a substance dockerized environment.

Options:
  -d    Activate debugging logs
  -y    Assume yes when prompted

Commands:

  subenv ls
  subenv init PATH/TO/PROJECT
  subenv use PROJECT
  subenv delete PROJECT
 
Samples: 

  subenv create 
    -b /substance
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
      api = SubenvAPI(self.options.base)

      if self.options.assumeYes:
        core.setAssumeYes(True)

      moduleName = 'substance.subenv.command.' + self.cmdString
      className = self.cmdString.title()

      logging.debug("Import %s, ClassName: %s", moduleName, className)

      module_ = import_module(moduleName)
      class_ = getattr(module_, className)
      self.command = class_(core=core, api=api)
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

      if arg in self.commands:
        i += 1
      else:
        parsed.append(arg)

    self.input = args
    self.commandInput = extraArgs

    (self.options, self.args) = self.parseShellInput()

    self.main()

def cli():
  prog = SubenvCLI()
  prog.execute(sys.argv)
