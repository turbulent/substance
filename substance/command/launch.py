from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Launch(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.launch) \
      .then(dinfo("Engine \"%s\" has been launched.", name)) \
      .catch(self.exitError)
