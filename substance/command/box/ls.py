from substance.monads import *
from substance.logs import *
from substance import (Command)
from tabulate import tabulate

logger = logging.getLogger(__name__)

class Ls(Command):
  def getShellOptions(self, optparser):
    #optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser

  def getUsage(self):
    return "substance box ls [options]"

  def getHelpTitle(self):
    return "List substance box available locally"

  def main(self):
    self.core.getBoxes() \
      .mapM(self.tabulateBox) \
      .bind(self.tabulateBoxes) \
      .catch(self.exitError) \
      .bind(logger.info)

  def tabulateBox(self, box):  
    return OK([box.namespace, box.name, box.version, box.registry, box.archiveSHA1])

  def tabulateBoxes(self, boxes):
    headers = ["NAMESPACE","NAME", "VERSION", "REGISTRY", "HASH"]
    table = tabulate(boxes, headers=headers, tablefmt="plain")
    return OK(table)

