from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.constants import Syncher

class Sync(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    optparser.add_option("-u","--up", dest="up", help="Synchronize UP to the engine only.", default=False, action="store_true")
    optparser.add_option("-d","--down", dest="down", help="Synchronize DOWN from the engine only.", default=False, action="store_true")
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

    if self.getOption('up'):
      direction = Syncher.UP
    elif self.getOption('down'):
      direction = Syncher.DOWN
    else:
      direction = Syncher.BOTH

    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(self.syncFolders, direction=direction) \
      .catch(self.exitError)

  def syncFolders(self, engine, direction=Syncher.BOTH):
    return engine.getSyncher().start(direction)
