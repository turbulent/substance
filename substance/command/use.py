from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Use(Command):
  def getShellOptions(self, optparser):
    #optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser

  def getUsage(self):
    return "substance use [options] ENGINE-NAME SUBENV-NAME"

  def getHelpTitle(self):
    return "Specify which engine and subenv is used by default"

  def main(self):
    name = self.getInputName()
    subenv = self.getArg(1)

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.core.setUse, subenvName=subenv) \
      .then(self.core.config.saveConfig) \
      .catch(self.exitError)
