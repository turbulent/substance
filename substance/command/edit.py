import logging
import os
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( EngineNotFoundError, SubstanceDriverError )

class Edit(Command):

  def getShellOptions(self, optparser):
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      cmd = os.environ.get('EDITOR', 'vi') + ' ' + engine.configFile
      Shell.call(cmd)

    except EngineNotFoundError:
      logging.info("Engine \"%s\" does not exist" % name) 
