from substance.monads import *
from substance.logs import *
from substance import (Command, Engine)
from tabulate import tabulate

logger = logging.getLogger(__name__)

class Ls(Command):
  def getShellOptions(self, optparser):
    #optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser

  def getUsage(self):
    return "substance engine ls [options]"

  def getHelpTitle(self):
    return "List substance engines"

  def main(self):
    self.core.getEngines() \
      .mapM(self.core.loadEngine) \
      .mapM(Engine.loadConfigFile) \
      .mapM(Engine.loadState) \
      .mapM(self.tabulateEngine) \
      .bind(self.tabulateEngines) \
      .catch(self.exitError) \
      .bind(logger.info)

  def tabulateEngine(self, engine):  
    state = engine.state if engine.state else "-"
    prov = "yes" if engine.isProvisioned() else "no"
    ip = engine.getPublicIP() if engine.getPublicIP() else "-"
    return OK([engine.getName(), prov, state, ip, "-"])

  def tabulateEngines(self, engines):
    headers = ["NAME", "PROVISIONED", "STATE", "IP", "ERRORS"]
    table = tabulate(engines, headers=headers, tablefmt="plain")
    return OK(table)

