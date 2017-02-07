from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

logger = logging.getLogger(__name__)

class Logs(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-n","--lines", dest="lines", help="Output the last N lines", default=None, metavar="N")
    optparser.add_option("-p","--pattern", dest="pattern", help="Use a log pattern instead of arguments", default=None)
    optparser.add_option("-l","--list", dest="list", help="List available environment logs", default=None, action="store_true")
    return optparser

  def getUsage(self):
    return "substance logs [options] [container] [logname]"

  def getHelpTitle(self):
    return "Display current subenv logs"

  def main(self):

    op = self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.envLoadCurrent) 

    if self.getOption('list'):
      op = op.bind(Engine.envListLogs, parts=self.getArgs(), pattern=self.getOption('pattern'))
    else:
      op = op.bind(Engine.envLogs, parts=self.getArgs(), pattern=self.getOption('pattern'), lines=self.getOption('lines')) 

    op = op.catch(self.exitError)
    return op
