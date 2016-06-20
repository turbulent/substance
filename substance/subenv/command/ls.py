import os
import logging
import shlex
from tabulate import tabulate

from substance.logs import *
from substance.exceptions import (InvalidOptionError)

from substance.subenv import (SubenvCommand, SPECDIR, SubenvAPI)

class Ls(SubenvCommand):

  def getUsage(self):
    return "subenv ls [options]"

  def getHelpTitle(self):
    return "Print a list of substance project environments."

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    return self.api.ls() \
      .mapM(self.tabulateEnv) \
      .bind(self.tabulateEnvs) \
      .catch(self.exitError) \
      .bind(logging.info) 

  def tabulateEnv(self, env):
    return OK([env.name, "X" if env.current else "", env.basePath, env.getLastAppliedDateTime('%B %d %Y, %H:%M:%S')])

  def tabulateEnvs(self, envs):
    headers = ["NAME", "CURRENT", "BASEPATH", "MODIFIED"]
    table = tabulate(envs, headers=headers, tablefmt="plain")
    return OK(table)
