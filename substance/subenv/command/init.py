import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)

from substance.subenv import (SubenvCommand, SPECDIR, SubenvAPI)

class Init(SubenvCommand):

  def getShellOptions(self, optparser):
    optparser.add_option("--name", type="str", dest="name", help="Envrionment name")
    optparser.add_option("--define", "-D", dest="define", default=[], action='append', help="Define a variable for the environment")
    return optparser

  def main(self):
    return Try.sequence([ self.readInputPath(), self.readInputEnv() ]) \
      .bind(lambda l: self.api.init(*l)) \
      .catch(self.exitError) \
      .bind(lambda e: logging.info("Environment '%s' initialized." % e.name)) 

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
      return Fail(InvalidOptionError("Please specify a path to a '%s' folder." % SPECDIR))
    path = os.path.abspath(os.path.normpath(self.args[0]))
    return OK(path)
