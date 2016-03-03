import logging
from substance.command import Command
from tabulate import tabulate

class Ls(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser

  def main(self):

    table = []
    headers = ["NAME", "PROVISIONED", "STATE", "URL", "ERRORS"]

    try:
      self.core.assertPaths()
    except Exception as err:
      self.exitError(err)

    engines = self.core.getEngines()
    for name in engines:
      engine = self.core.getEngine(name)
      engine.readConfig()
      state = engine.state()
      state = state if state else "-"
      prov = "yes" if engine.isProvisioned() else "no"
      table.append([engine.getName(), prov, state, engine.getDockerURL(), ""])

    logging.info(tabulate(table, headers=headers, tablefmt="plain"))
