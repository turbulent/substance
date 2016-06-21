import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)
from substance import Command
from substance.subenv import (SPECDIR, SubenvAPI)

class Delete(Command):

  def getUsage(self):
    return "subenv delete [ENV NAME]"

  def getHelpTitle(self):
    return "Permanently delete a project environment"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.readInputName().catch(self.exitError).getOK()
    return self.api.exists(name) \
      .thenIfFalse(defer(self.exitError, "Environment '%s' does not exist." %  name)) \
      .then(defer(self.ask, "You are about to delete subenv \"%s\"" % name)) \
      .then(defer(self.api.delete, name)) \
      .catch(self.exitError)

  def readInputName(self):
    if len(self.args) <= 0:
      return Fail(InvalidOptionError("Please specify the name of a subenv."))
    name = os.path.normpath(self.args[0])
    return OK(name)
