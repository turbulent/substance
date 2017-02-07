from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Restart(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "substance restart [options] [CONTAINER...]"

  def getHelpTitle(self):
    return "Restart all or specified container(s)"

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envRestart, time=self.getOption('time'), containers=self.args) \
      .catch(self.exitError)
