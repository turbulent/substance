from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.constants import (EngineStates)
from substance.exceptions import (EngineNotRunning)

logger = logging.getLogger(__name__)

class Status(Command):
  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "substance status [options]"

  def getHelpTitle(self):
    return "Show substance engine and env status"

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envStatus, full=True) \
      .bind(self.printStatus) \
      .catch(self.exitError)

  def printStatus(self, envStatus):
    engine = envStatus.get('engine')
    containers = envStatus.get('containers')

    headers = ["ENGINE", "SUBENV"]
    cols = [[ engine.name, engine.currentEnv ]]
    table = tabulate(cols, headers=headers, tablefmt="plain")

    logger.info(table)
    if containers:
      logger.info("")
      logger.info(containers)
    return OK(None)

