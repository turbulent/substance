from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Sync(Command):
  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "substance sync [options] [CONTAINER...]"

  def getHelpTitle(self):
    return "Synchronize & watch the devroot of the current engine"

  def getHelpDetails(self):
    return """
This process will run in the foreground and monitor local and remove file system events to perform
synchronization over SSH with rsync both ways. When working locally ; activate the sync command to keep
your code up to date on the engine or to receive artifact stored in the devroot in your local folders.
"""

  def main(self):
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(self.syncFolders) \
      .catch(self.exitError)

  def syncFolders(self, engine):
    return engine.getSyncher().start()
