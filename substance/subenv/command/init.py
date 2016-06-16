import os
import logging
import shlex

from substance.logs import *
from substance import Command
from substance.exceptions import (InvalidOptionError)

from substance.subenv import SubenvAPI

class Init(Command):

  def getShellOptions(self, optparser):
    optparser.add_option('--base', "-b", dest="base", help="Path to the base", default="/substance")
    optparser.add_option("--devroot", "-d", dest="devroot", help="Path to the devroot directory.")
    optparser.add_option("--define", "-D", dest="define", default=[], action='append', help="Define a variable for the environment")
    optparser.add_option("--name", type="str", dest="name", help="Envrionment name")
    return optparser

  def main(self):
    api = SubenvAPI(self.options.base, self.options.devroot)
    return Try.sequence([ self.readInputPath(), self.readInputEnv() ]) \
      .bind(lambda l: api.init(*l)) \
      .catch(self.exitError)

  def readInputEnv(self): 
    env = {}
    envopts = self.options.define
    for opt in envopts:
      if opt.index('=') == 01:
        return Fail(InvalidOptionError("%s is not a valid define. Use VAR=val form." % opt))
      (var, val) = ''.join(shlex.split(opt)).split('=')
      env[var] = val
    return OK(env) 

  def readInputPath(self):
    if len(self.args) <= 0:
      return Fail(InvalidOptionError("Please specify a path to a %s folder." % SubenvAPI.DIR))
    path = self.args[0]
    return OK(path)

