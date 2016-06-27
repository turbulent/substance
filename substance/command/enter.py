from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.command.command import PassThroughParser

class Enter(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    return optparser

  def getUsage(self):
    return "substance enter [options] COMMAND"

  def getHelpTitle(self):
    return "Enter a container by spawning a bash shell"

  def main(self):
    container = self.getInputContainer()
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envEnter, container=container) \
      .catch(self.exitError)

  def getInputContainer(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify a container name.")
    name = self.args[0]
    return name

