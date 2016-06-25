import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance import Command
from substance.subenv import (SPECDIR, SubenvAPI)

logger = logging.getLogger(__name__)

class Current(Command):

  def getUsage(self):
    return "subenv current"

  def getHelpTitle(self):
    return "Print the current subenv on stdout"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    return self.api.current() \
      .thenIfNone(defer(self.exitError, "No current subenv is active.")) \
      .catch(self.exitError) \
      .bind(self.printEnv)

  def printEnv(self, envSpec):
    logger.info(envSpec.name)
