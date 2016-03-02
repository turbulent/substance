import sys
import os
import logging
from optparse import OptionParser
from getpass import getpass

class Command:
  options = {}
  args = []
  core = None

  def __init__(self, core=None):
    self.core = core

  def help(self) :
    """Returns the help description for this particular command"""
    pass

  def getUsage(self) :
    return "command: USAGE [options]"
  
  def parseShellInput(self) :
    """Return the options and arguments for this command as a tuple"""

    usage = self.getUsage()
    parser = OptionParser(usage=usage, conflict_handler="resolve")
    self.getShellOptions(parser)

    (opts, args) =  parser.parse_args(self.input)

    return (opts, args)

  def getShellOptions(self, optparser):
    optparser.add_option("-h", "--help", dest="help", help="Help about this command", action="store_true", default=False)
    return optparser
 
  def main(self) :
    """The main function body"""
    pass
  
  def getOptions(self) :
    return self.options
  
  def hasOption(self, key) :
    if hasattr(self.options, key):
      return True
  
  def getOption(self, key) :
    if self.hasOption(key):
      return getattr(self.options, key, None)
    return None
  
  def getArgs(self) :
    return self.args

  def hasArg(self, argno) :
    if len(self.args) < argno:
      return None
    return True 
  
  def getArg(self, argno) :
    if self.hasArg(Argno):   
      return self.args[argno]
    return None
 
  def read(self, msg="") :
    return raw_input(msg)
  
  def readln(self, msg="") :
    return raw_input(msg + "\n")
  
  def readpwd(self, msg="") :
    return getpass(msg)
  
  def readpwdln(self, msg="") :
    return getpass(msg + "\n")
  
  def exitOK(self, msg=None) :
    if msg:
      logging.info(msg)
    sys.exit(0)
 
  def exitHelp(self, msg=None, code=1):
    logging.info(self.getHelp())
    logging.info("")
    logging.info(msg)
    sys.exit(1)
 
  def exitError(self, msg=None, code=1) :
    if msg:
      logging.error(msg)  
    sys.exit(1)
  
  def execute(self, args=None) :
    if args == None:
      args = sys.argv[1:]
  
    self.input = args 
    (self.options,self.args) = self.parseShellInput()
    self.main()
