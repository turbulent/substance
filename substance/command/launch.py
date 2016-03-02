import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( EngineNotFoundError, SubstanceDriverError )

class Launch(Command):

  def getShellOptions(self, optparser):
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)
      engine.readConfig()
      engine.launch()

      logging.info("The VM of engine \"%s\" has been launched." % name)
    except EngineNotFoundError:
      logging.info("Engine \"%s\" does not exist" % name) 
    except Exception as err:
      logging.error("Failed to launch engine VM \"%s\": %s" % (name, err))
