from substance.monads import *
from substance.logs import *
from substance.command import (Command)
from substance.engine import (Engine)
from tabulate import tabulate

class Ls(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser

  def main(self):
    self.core.assertPaths() \
      .then(self.core.getEngines) \
      .mapM(self.core.loadEngine) \
      .mapM(Engine.loadConfigFile) \
      .mapM(Engine.loadState) \
      .mapM(self.tabulateEngine) \
      .bind(self.tabulateEngines) \
      .catch(self.exitError) \
      .bind(logging.info)

  def tabulateEngine(self, engine):  
    state = engine.state if engine.state else "-"
    prov = "yes" if engine.isProvisioned() else "no"
    dockerURL = engine.getDockerURL()
    return OK([engine.getName(), prov, state, dockerURL, "-"])

  def tabulateEngines(self, engines):
    headers = ["NAME", "PROVISIONED", "STATE", "URL", "ERRORS"]
    table = tabulate(engines, headers=headers, tablefmt="plain")
    return OK(table)

