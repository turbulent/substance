from substance.monads import *
from substance.logs import *
from substance.engine import Engine
from substance.command import Command
from substance.exceptions import (SubstanceError)

class Ssh(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.shell) \
      .catch(self.exitError)
