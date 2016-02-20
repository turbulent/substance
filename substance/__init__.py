import sys
import traceback
import logging
import re
import yaml
from importlib import import_module
from optparse import OptionParser
from substance.command import Command

class Substance(Command):

  def setupLogging(self):
    log_level = logging.DEBUG if self.options.debug else logging.INFO 
    logging.basicConfig(format='%(message)s', level=log_level)

  def setupEnv(self): 
    """Setup the Environment """

  def getShellOptions(self, optparser):
    Command.getShellOptions(self, optparser)

    optparser.add_option("-a", dest="allc", help="Operate on all defined containers", action="store_true", default=False)
    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-t", dest="term", help="Allocate a pseudo-TTY", default=False, action="store_true")
    optparser.add_option("-i", dest="interactive", help="Keep STDIN open even if not attached", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelp(self):
    helpUsage = """
Usage: substance COMMAND [options] [CONTAINERS..]

substance - Local dockerized development environment.

Options:
  -f            Alternate config file location. defaults to containers.yml
  -a		Operate on all defined containers.
  -d		Activate debugging logs
  -t		Allocate a pseudo-TTY
  -i		Keep STDIN open even if not attached

Commands:
  create        Create the specified container(s)
  start         Start the specified container(s)
  stop          Stop the specified container(s)
  remove        Remove the specified container(s). Stop if needed.

  restart       Stop and then Start a container.
  recreate      Remove and then Start a container.

  exec          Exec a command on a container
  status        Output container status
  stats         Output live docker container stats
 
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
      moduleName = 'substance.'+self.cmdString
      className = self.cmdString.title()

      logging.debug("Import %s\nClassName: %s" % (moduleName, className))

      module_ = import_module(moduleName)
      class_ = getattr(module_, className)
      self.command = class_()
    except ImportError, err:
      logging.debug("%s" % err)
      self.exitError("Unrecognized command %s" % self.cmdString)

    try:
      self.command.execute(self.commandInput)
    except Exception as err:
      logging.error(traceback.format_exc())
      self.exitError("Error running command %s: %s" % (self.cmdString, err), code=2)

  def execute(self, args=None) :

    args.pop(0)

    parsed = []
    extra_args = []
    i = 0
    for arg in args:
      if i >= 1:
        extra_args.append(arg)
        continue
  
      if (arg[0] == '-' or arg[0:2] == '--'):
        parsed.append(arg)
      else:
        parsed.append(arg)
        i+=1
  
    #print("Top Level Input: %s" % parsed)
    #print("Command Input: %s" % extra_args)

    self.input = parsed
    self.commandInput = extra_args

    (self.options,self.args) = self.parseShellInput()
    self.main()

def main():
  subst = Substance()
  subst.execute(sys.argv)
