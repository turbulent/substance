import logging
from substance.logs import *
from substance.monads import *
from substance.command import Command
from substance.engine import Engine
from substance.shell import Shell
from substance.exceptions import (SubstanceError, EngineNotProvisioned)

class Delete(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.deprovision) \
      .catchError(EngineNotProvisioned, lambda e: OK(None)) \
      .then(defer(self.core.removeEngine, name)) \
      .then(dinfo("Engine \"%s\" has been deleted.", name)) \
      .catch(self.exitError)

