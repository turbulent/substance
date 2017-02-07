from __future__ import absolute_import

import sys
import os
import re
import logging
import pkgutil
import importlib
import traceback
from collections import OrderedDict
from importlib import import_module
import optparse
from getpass import getpass

from substance import Shell
from substance.exceptions import InvalidCommandError

logger = logging.getLogger('substance')

class Parser(optparse.OptionParser):
  pass
#  def format_description(self, formatter):
#    return self.description if self.description else ""
  def format_epilog(self, formatter):
    return "\n"+self.epilog if self.epilog else ""


class PassThroughParser(Parser):
  def _process_long_opt(self, rargs, values):
    try:
      optparse.OptionParser._process_long_opt(self, rargs, values)
    except optparse.BadOptionError, err:
      self.largs.append(err.opt_str)

  def _process_short_opts(self, rargs, values):
    try:
      optparse.OptionParser._process_short_opts(self, rargs, values)
    except optparse.BadOptionError, err:
      self.largs.append(err.opt_str)

class CLI(object):
  def __init__(self):
    self.args = None
    self.options = None
    self.input = None
    self.parser = None
    self.name = None
    self.parent = None
    
  def getHelp(self):
    """Returns the help description for this particular command"""
    return self.getParser().format_help()

  def getHelpTitle(self):
    return ""

  def getHelpDetails(self):
    return ""

  def getUsage(self):
    return "command: USAGE [options]"

  def getParserClass(self):
    return Parser

  def getParser(self, interspersed=True):
    usage = self.getUsage()
    parserClass = self.getParserClass()
    parser = parserClass(usage=usage, conflict_handler="resolve", add_help_option=False, description=self.getHelpTitle(), epilog=self.getHelpDetails())
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
    return optparser

  def execute(self, args=None):
    self.input = args
    (self.options, self.args) = self.parseShellInput()
    return self.main()

  def initialize(self):
    pass

  def main(self):
    """The main function body"""
    pass

  def getOptions(self):
    return self.options

  def hasOption(self, key):
    if self.options and hasattr(self.options, key):
      return True

  def getOption(self, key):
    if self.hasOption(key):
      return getattr(self.options, key, None)
    return None

  def getArgs(self):
    return self.args

  def hasArg(self, argno):
    if len(self.args) < argno + 1:
      return False
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
      logger.info(msg)
    sys.exit(0)

  def exitHelp(self, msg=None, code=1):
    logger.info(self.getHelp())
    logger.info("")
    if msg:
      logger.info(msg)
    sys.exit(1)

  def exitError(self, msg=None, code=1):
    if msg and isinstance(msg, Exception):
      logger.error("%s (%s)" % (msg, type(msg).__name__))
    elif msg:
      logger.error(msg)
    sys.exit(1)


class Program(CLI):
  def __init__(self):
    super(Program, self).__init__()
    self.cmdString = None
    self.commandInput = None
    self.command = None
    self.core = None
    self.commands = OrderedDict()
    self.addCommand('help', 'substance.command.help')

  def setupCommands(self):
    pass
    
  def getCommands(self):
    k = self.commands.keys()
    v = map(lambda x: self.getCommand(x), k)
    return OrderedDict(zip(k, v))

  def getCommand(self, commandName):
    if commandName in self.commands:
      commandModule = self.commands[commandName]
      commandClass = commandName.title()
    else:
      commandModule = 'substance.command.fallback'
      commandClass = 'Fallback'
 
    module_ = importlib.import_module(commandModule)
    class_ = getattr(module_, commandClass)
    command = class_()
    command.parent = self
    command.name = commandName
    return command

  def addCommand(self, commandName, commandModule):
    if commandName in self.commands:
      raise ValueError("Command '%s' is already registered." % commandName)
    self.commands[commandName] = commandModule
 
  def removeCommand(self, commandName):
    if commandName not in self.commands:
      raise ValueError("Command '%s' is not registered." % commandName)
    self.commands.pop(commandName, None)

  def getHelpDetails(self):
    helpUsage = "Commands:\n\n"
    for name, command in self.getCommands().iteritems():
      helpUsage += "  %-20s%s\n" % (name, command.getHelpTitle())
    return helpUsage

  def setupEnv(self):
    """Setup the Environment """

  def setupLogging(self):
    if self.getOption('debug'):
      logging.getLogger('substance').handlers[0].setLevel(logging.DEBUG)
      logging.getLogger('subwatch').setLevel(logging.DEBUG)
      logging.getLogger('watchdog').setLevel(logging.INFO)
      logging.getLogger('paramiko').setLevel(logging.INFO)

  def execute(self, args=None):
    self.input = args
    (self.options, self.args) = self.parseShellInput(False)
    self.main()

  def initialize(self):  
    self.setupLogging()
    self.setupEnv()
    self.setupCommands()

  def main(self):
    try:
      self.initialize()

      if not len(self.args) > 0:
        self.cmdString = 'help'
        self.commandInput = []
        #self.exitError("Please provide a command.\n\nUse 'help' for available commands.")
      else: 
        self.cmdString = self.args[0]
        self.commandInput = self.args[1:]

      self.runCommand(self.cmdString)
    except Exception as err:
      logger.error(traceback.format_exc())
      self.exitError("Error running command %s: %s" % (self.cmdString, err), code=2)

  def runCommand(self, commandName):
    command = self.getCommand(commandName)
    self.command = self.initCommand(command)
    self.command.execute(self.commandInput)

class Command(CLI):

  def __init__(self):
    super(Command, self).__init__()

  def ask(self, msg):
    return Shell.printConfirm(msg, assumeYes=self.core.getAssumeYes())

  #---- Validation Helpers

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

class SubProgram(Program):
  def initialize(self):
    self.setupCommands()

