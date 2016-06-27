from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.command.command import PassThroughParser

class Exec(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    optparser.add_option("-i","--interactive", dest="interactive", help="Interactive command", default=None, action="store_true")
    return optparser

  def getUsage(self):
    return "substance exec [options] CONTAINER COMMAND..."

  def getHelpTitle(self):
    return "Exec a command within a container"

  def main(self):
    container = self.getInputContainer()
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envExec, container=container, interactive=self.getOption('interactive'), cmd=' '.join(self.args[1:])) \
      .catch(self.exitError)

  def getInputContainer(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify a container name.")
    name = self.args[0]
    return name

