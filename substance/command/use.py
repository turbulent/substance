from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Use(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-e", "--env", dest="env", help="Also switch to this environment", default=False)
    return optparser

  def getUsage(self):
    return "substance use [options] ENGINE-NAME"

  def getHelpTitle(self):
    return "Specify which engine is used by default"

  def main(self):
    name = self.getInputName()
    return self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(self.core.setUse, subenvName=self.getOption('env')) \
      .then(self.core.config.saveConfig) \
      .catch(self.exitError)
