from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate
from substance.constants import (EngineStates)
from substance.exceptions import (EngineNotRunning)

logger = logging.getLogger(__name__)


class Cleanup(Command):

    def getUsage(self):
        return "substance cleanup [options]"

    def getHelpTitle(self):
        return "Cleanup unused images and containers"

    def main(self):
        return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
            .bind(Engine.envLoadCurrent) \
            .bind(Engine.envCleanup) \
            .catch(self.exitError)
