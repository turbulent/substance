import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)

from substance.subenv import (SubenvCommand, SPECDIR, SubenvAPI)

class Use(SubenvCommand):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.readInputName().catch(self.exitError).getOK()
    return self.api.exists(name) \
      .thenIfFalse(defer(self.exitError, "Environment '%s' does not exist." %  name)) \
      .then(defer(self.api.use, name))  \
      .catch(self.exitError)

  def readInputName(self):
    if len(self.args) <= 0:
      return Fail(InvalidOptionError("Please specify the name of a subenv."))
    name = os.path.normpath(self.args[0])
    return OK(name)
