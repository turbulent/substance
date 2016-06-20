from __future__ import absolute_import

import sys
import os
import re
import logging
from optparse import OptionParser
from getpass import getpass

from substance import Shell

class Command(object):

  def __init__(self, core=None):
    self.options = {}
    self.args = []
    self.input = None
    self.core = core
    self.parser = None

  def help(self):
    """Returns the help description for this particular command"""
    pass

  def getUsage(self):
    return "command: USAGE [options]"

  def getParser(self, interspersed=True):
    usage = self.getUsage()
    parser = OptionParser(usage=usage, conflict_handler="resolve")
    self.getShellOptions(parser)
    if interspersed:
      parser.enable_interspersed_args()
    else:
      parser.disable_interspersed_args()
    return parser
  
  def parseShellInput(self, interspersed=True):
    """Return the options and arguments for this command as a tuple"""
    usage = self.getUsage()
    parser = self.getParser(interspersed)
    (opts, args) = parser.parse_args(self.input)
    return (opts, args)

  def getShellOptions(self, optparser):
    optparser.add_option("-h", "--help", dest="help", help="Help about this command", action="store_true", default=False)
    return optparser

  def main(self):
    """The main function body"""
    pass

  def getOptions(self):
    return self.options

  def hasOption(self, key):
    if hasattr(self.options, key):
      return True

  def getOption(self, key):
    if self.hasOption(key):
      return getattr(self.options, key, None)
    return None

  def getArgs(self):
    return self.args

  def hasArg(self, argno):
    if len(self.args) < argno:
      return None
    return True

  def getArg(self, argno):
    if self.hasArg(argno):
      return self.args[argno]
    return None

  def read(self, msg=""):
    return raw_input(msg)

  def readln(self, msg=""):
    return raw_input(msg + "\n")

  def readpwd(self, msg=""):
    return getpass(msg)

  def readpwdln(self, msg=""):
    return getpass(msg + "\n")

  def exitOK(self, msg=None):
    if msg:
      logging.info(msg)
    sys.exit(0)

  def exitHelp(self, msg=None, code=1):
    logging.info(self.getHelp())
    logging.info("")
    logging.info(msg)
    sys.exit(1)

  def exitError(self, msg=None, code=1):
    if msg and isinstance(msg, Exception):
      logging.error("%s (%s)" % (msg, type(msg).__name__))
    elif msg:
      logging.error(msg)
    sys.exit(1)

  def execute(self, args=None):
    if args == None:
      args = sys.argv[1:]

    self.input = args
    (self.options, self.args) = self.parseShellInput()
    self.main()

  def ask(self, msg):
    return Shell.printConfirm(msg, assumeYes=self.core.getAssumeYes())

  #---- Validation

  def getInputName(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify an engine name.")
      
    name = self.args[0]
    if not name or not self.validateEngineName(name):
      return self.exitError("Invalid name specified. Please use only letters, numbers, dash or underscores.")
    return name

  def validateEngineName(self, name):
    return bool(re.match(r'^[a-zA-Z0-9\-_]*$', name))

  def validateDriver(self, driver):
    return self.core.validateDriver(driver)

  def validateInteger(self, value):
    try:
      val = int(value)
      return True
    except ValueError:
      return False


