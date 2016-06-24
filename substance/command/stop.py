from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Stop(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    return optparser

  def getUsage(self):
    return "substance stop [options]"

  def getHelpTitle(self):
    return "Stop containers in the current subenv"

  def main(self):
   
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envStop, containers=self.args) \
      .catch(self.exitError)

