from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.constants import (EngineStates)
from substance.exceptions import (EngineNotRunning)

class Status(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-f","--full", dest="full", help="Engine to run this command on", default=None, action="store_true")
    return optparser

  def getUsage(self):
    return "substance status [options]"

  def getHelpTitle(self):
    return "Show substance engine and env status"

  def main(self):
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envStatus, full=self.getOption('full')) \
      .bind(self.printStatus) \
      .catch(self.exitError)

  def printStatus(self, envStatus):
    engine = envStatus.get('engine')
    containers = envStatus.get('containers')

    headers = ["ENGINE", "SUBENV"]
    cols = [[ engine.name, engine.currentEnv ]]
    table = tabulate(cols, headers=headers, tablefmt="plain")

    logging.info(table)
    logging.info("")
    logging.info(containers)
    return OK(None)

