from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

class Switch(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    optparser.add_option("-r","--restart", dest="restart", help="Once switched, restart containers", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "substance switch [options] SUBENV-NAME"

  def getHelpTitle(self):
    return "Switch the active subenv for an engine"

  def main(self):
    subenv = self.getArg(0)
    if not subenv:
      return self.exitError("Please specify a subenv name to switch to.")

    self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envSwitch, subenvName=subenv, restart=self.getOption('restart')) \
      .catch(self.exitError)
