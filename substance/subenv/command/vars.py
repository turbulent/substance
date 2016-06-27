import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance import Command
from substance.subenv import (SPECDIR, SubenvAPI)

class Vars(Command):

  def getUsage(self):
    return "subenv vars [ENV NAME?]"

  def getHelpTitle(self):
    return "Output the vars for an env on stdout"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.readInputName().getOK()
    return self.api.vars(name) \
      .bind(self.printEnvVars) \
      .catch(self.exitError) 

  def printEnvVars(self, vars=None):
    vars = {} if not vars else vars
    for k, v in vars.iteritems():
      print("%s=\"%s\"" % (k, v))
    return OK(None)
        
  def readInputName(self):
    if len(self.args) > 0:
      name = os.path.normpath(self.args[0])
      return OK(name)
    else:
      return OK(None)
