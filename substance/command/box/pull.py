import logging
from substance.logs import *
from substance.monads import *
from substance import (Command, Box, Shell)
from substance.exceptions import (SubstanceError)

class Pull(Command):

  def getUsage(self):
    return "substance box pull [BOXSTRING]"

  def getHelpTitle(self):
    return "Download a box"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.getInputName() 
    return self.core.readBox(name) \
      .bind(self.core.pullBox) \
      .then(dinfo("Box \"%s\" has been pulled.", name)) \
      .catch(self.exitError)

  def getInputName(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify a box string.")
    name = self.args[0]
    return name
