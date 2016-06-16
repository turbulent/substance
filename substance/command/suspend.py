from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from substance.exceptions import (SubstanceError)

class Suspend(Command):
  def main(self):
    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.suspend) \
      .catch(self.exitError)
