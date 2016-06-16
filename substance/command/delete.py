import logging
from substance.logs import *
from substance.monads import *
from substance import (Command, Engine, Shell)
from substance.exceptions import (SubstanceError, EngineNotProvisioned)

class Delete(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.ask, "You are about to delete engine \"%s\"" % name)) \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.deprovision) \
      .catchError(EngineNotProvisioned, lambda e: OK(None)) \
      .then(defer(self.core.removeEngine, name)) \
      .then(dinfo("Engine \"%s\" has been deleted.", name)) \
      .catch(self.exitError)

