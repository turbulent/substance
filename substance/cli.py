from __future__ import absolute_import

import sys
import logging
import traceback
from optparse import OptionParser

from substance import (Command, Core)

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
    helpUsage = """
Commands:

  # Engine commands

  ls              List engines
  init            Initialize a new engine
  delete          Delete an engine
  launch          Launch an existing engine
  stop            Stop a running engine
  suspend         Suspend a running engine
  deprovision     Destroy the VM associated with an engine
  ssh             Open an interactive shell with SSH on an engine
  sshinfo         Output SSH connection info for an engine
  env             Output the shell variables for connecting to the engine's docker daemon.

  help            Help and usage information on commands
   
  # Task Control
  substance task mybox load rsi-website
  substance task mybox status -a
  substance task mybox start -a
  substance task mybox stop -a
  substance task mybox remove -a
  substance task mybox recreate -a
  substance enter mybox myboxweb
  

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


def cli():
  prog = SubstanceCLI()
  prog.execute(sys.argv)
