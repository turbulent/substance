from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

logger = logging.getLogger(__name__)

class Logs(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-f","--follow", dest="follow", help="Keep following the logs", default=None, action="store_true")
    optparser.add_option("-n","--lines", dest="lines", help="Output the last N lines", default=None, metavar="N")
    return optparser

  def getUsage(self):
    return "substance logs [options] PATTERN"

  def getHelpTitle(self):
    return "Display current subenv logs"

  def main(self):
    pattern = self.getInputPattern()
    return self.core.loadCurrentEngine(name=self.getOption('engine')) \
      .bind(Engine.envLoadCurrent) \
      .bind(Engine.envLogs, pattern=pattern, follow=self.getOption('follow'), lines=self.getOption('lines')) \
      .catch(self.exitError)

  def getInputPattern(self):
    if not self.hasArg(0):
      self.exitError("You must specified a log pattern.")

    return self.getArg(0)
