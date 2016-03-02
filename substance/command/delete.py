import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( EngineNotFoundError, SubstanceDriverError )

class Delete(Command):

  def getShellOptions(self, optparser):
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      if not self.core.getConfigKey('assumeYes') and not Shell.printConfirm("You are about to delete engine \"%s\"." % name):
        self.exitOK("User cancelled.")
    
      engine.deprovision() 

      logging.info("Engine \"%s\" has been deprovisioned.")
    except EngineNotFoundError:
      logging.info("Engine \"%s\" does not exist" % name) 
    except SubstanceDriverError:
      logging.info("No VM is currently launched for engine \"%s\"" % name)
      pass
    except Exception as err:
      logging.error("Failed to deprovision engine VM \"%s\": %s" % (name, err))
