from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Start(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-r","--reset", dest="reset", help="Stop & remove all containers before starting", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "substance start [options] [CONTAINER...]"

  def getHelpTitle(self):
    return "Start all or specific container(s)"

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envStart, reset=self.getOption('reset'), containers=self.args) \
      .catch(self.exitError)
