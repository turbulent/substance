import os

from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from substance.exceptions import (SubstanceError)
from substance.syncher import SubwatchSyncher
from substance.constants import Syncher

class Sync(Command):

  def getUsage(self):
    return "substance engine sync [ENGINE NAME]"

  def getHelpTitle(self):
    return "Synchronize and watch the devroot folder for an engine"

  def getHelpDetails(self):
    return """
This process will run in the foreground and monitor local and remove file system events to perform
synchronization over SSH with rsync both ways. When working locally ; activate the sync command to keep
your code up to date on the engine or to receive artifact stored in the devroot in your local folders.
"""

  def getShellOptions(self, optparser):
    optparser.add_option("-u","--up", dest="up", help="Synchronize UP to the engine only.", default=False, action="store_true")
    optparser.add_option("-d","--down", dest="down", help="Synchronize DOWN from the engine only.", default=False, action="store_true")
    return optparser

  def main(self):

    direction = Syncher.BOTH
    if self.getOption('up'):
      direction = Syncher.UP
    elif self.getOption('down'):
      direction = Syncher.DOWN

    name = self.getInputName()

    self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(self.syncFolders, direction=direction) \
      .catch(self.exitError)

  def syncFolders(self, engine, direction):
    return engine.getSyncher().start(direction)
