from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Recreate(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "substance recreate [options] [CONTAINER...]"

  def getHelpTitle(self):
    return "Recreate all or specified container(s)"

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envRecreate, containers=self.args, time=self.getOption('time')) \
      .catch(self.exitError)
