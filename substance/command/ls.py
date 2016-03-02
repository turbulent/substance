# -*- coding: utf-8 -*-
# $Id$

import logging
from substance.command import Command
from substance.shell import Shell
from tabulate import tabulate

class Ls(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-a", dest="all", help="Single Val", action="store_true", default=False)
    return optparser
 
  def main(self):
   
    table = []
    headers = ["NAME", "ACTIVE", "STATE", "URL", "ERRORS"]

    try:
      self.core.assertPaths()
    except Exception as err:
      self.exitError(err)
      

    engines = self.core.getEngines()
    for name in engines:
      engine = self.core.getEngine(name)
      config = engine.readConfig()
      table.append([engine.getName(), "-", "-", engine.getDockerURL(), ""])


    logging.info(tabulate(table, headers=headers, tablefmt="plain"))
