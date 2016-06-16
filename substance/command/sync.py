import os

from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from substance.exceptions import (SubstanceError)
from substance.syncher import SubstanceSyncher

class Sync(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.syncFolders) \
      .catch(self.exitError)

  def syncFolders(self, engine):
    return engine.getSyncher().start()
