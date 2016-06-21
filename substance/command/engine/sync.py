import os

from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from substance.exceptions import (SubstanceError)
from substance.syncher import SubstanceSyncher

class Sync(Command):

  def getUsage(self):
    return "substance sync [ENGINE NAME]"

  def getHelpTitle(self):
    return "Synchronize and watch the devroot folder for an engine"

  def getHelpDetails(self):
    return """
This process will run in the foreground and monitor local and remove file system events to perform
synchronization over SSH with rsync both ways. When working locally ; activate the sync command to keep
your code up to date on the engine or to receive artifact stored in the devroot in your local folders.
"""

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
