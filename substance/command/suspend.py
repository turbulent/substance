from substance.command import Command
from substance.exceptions import (SubstanceError)
from substance.monads import *
from substance.logs import *
from substance.engine import Engine

class Suspend(Command):
  def main(self):
    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.suspend) \
      .catch(self.exitError)
