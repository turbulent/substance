import logging
from substance.logs import *
from substance.monads import *
from substance import (Command, Box, Shell)
from substance.exceptions import (SubstanceError)

class Delete(Command):

  def getUsage(self):
    return "substance box delete [BOXSTRING]"

  def getHelpTitle(self):
    return "Permanently delete a box."

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.getInputName()
    self.ask("You are about to delete box \"%s\"" % name) \
      .then(defer(self.core.readBox, name)) \
      .bind(self.core.removeBox) \
      .then(dinfo("Box \"%s\" has been deleted.", name)) \
      .catch(self.exitError)

  def getInputName(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify a box string.")

    name = self.args[0]
    return name
