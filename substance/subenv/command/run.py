import os
import logging
import shlex
import sys

from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance import Command
from substance.subenv import (SPECDIR, SubenvAPI)

logger = logging.getLogger(__name__)

class Run(Command):

  def getUsage(self):
    return "subenv run"

  def getHelpTitle(self):
    return "Run a command in the current subenv directory"

  def getShellOptions(self, optparser):
    return optparser

  def parseShellInput(self, interspersed=True):
    """Disable parsing for this run command"""
    usage = self.getUsage()
    parser = self.getParser(interspersed)
    (opts, args) = parser.parse_args([])
    return (opts, args)

  def main(self):
    return self.api.run(args=self.input) \
      .catch(self.exitError) 
