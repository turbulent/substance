import os
import logging
import shlex

from substance.logs import *
from substance.exceptions import (InvalidOptionError)

from substance.subenv import (SubenvCommand, SPECDIR, SubenvAPI)

class Delete(SubenvCommand):

  def getShellOptions(self, optparser):
    optparser.add_option("--name", type="str", dest="name", help="Envrionment name")
    optparser.add_option("--define", "-D", dest="define", default=[], action='append', help="Define a variable for the environment")
    return optparser

  def main(self):
    name = self.readInputName().catch(self.exitError).getOK()
    return self.api.exists(name) \
      .thenIfFalse(defer(self.exitError, "Environment '%s' does not exist." %  name)) \
      .then(defer(self.ask, "You are about to delete subenv \"%s\"" % name)) \
      .then(defer(self.api.delete, name))

  def readInputName(self):
    if len(self.args) <= 0:
      return Fail(InvalidOptionError("Please specify the name of a subenv."))
    name = os.path.normpath(self.args[0])
    return OK(name)
