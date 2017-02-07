from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Stop(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "substance stop [options]"

  def getHelpTitle(self):
    return "Stop all or specific container(s)"

  def main(self):
   
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envStop, containers=self.args, time=self.getOption('time')) \
      .catch(self.exitError)

