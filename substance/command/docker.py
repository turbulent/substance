from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.command.command import PassThroughParser

class Docker(Command):

  def getParserClass(self):
    return PassThroughParser

  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "substance docker [options] COMMAND"

  def getHelpTitle(self):
    return "Run a docker command on an engine"

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envDocker, command=' '.join(self.args)) \
      .catch(self.exitError)
