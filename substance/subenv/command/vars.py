import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance import Command
from substance.subenv import (SPECDIR, SubenvAPI)

class Vars(Command):

  def getUsage(self):
    return "subenv vars [options] [VAR1 VAR2...?]"

  def getHelpTitle(self):
    return "Output the vars for an env on stdout, optionally filtered"

  def getShellOptions(self, optparser):
    optparser.add_option("-e", "--env", dest="env", help="Specify an environment name")
    return optparser

  def main(self):
    name = self.readInputName().getOK()
    return self.api.vars(name, vars=self.getInputVars()) \
      .bind(self.printEnvVars) \
      .catch(self.exitError) 

  def printEnvVars(self, vars=None):
    vars = {} if not vars else vars
    for k, v in vars.iteritems():
      print("%s=\"%s\"" % (k, v))
    return OK(None)
      
  def getInputVars(self):
    if len(self.args) > 0:
      return self.args
    return None
  
  def readInputName(self):
    if self.getOption('env'):
      name = os.path.normpath(self.getOption('env'))
      return OK(name)
    else:
      return OK(None)
