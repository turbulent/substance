# -*- coding: utf-8 -*-
# $Id$

import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( EngineNotFoundError, EngineNotProvisioned, SubstanceDriverError )

class Deprovision(Command):

  def getShellOptions(self, optparser):
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      if not self.core.getConfigKey('assumeYes') and not Shell.printConfirm("You are about to deprovision engine VM \"%s\"." % name):
        self.exitOK("User cancelled.")
   
      engine.readConfig() 
      engine.deprovision() 

      logging.info("Engine \"%s\" has been deprovisioned.")

    except EngineNotFoundError:
      self.exitError("Engine \"%s\" does not exist" % name) 
    except EngineNotProvisioned:
      self.exitError("Engine \"%s\" is not currently provisioned." % name)
    except SubstanceDriverError as err:
      self.exitError("Failed to deprovision engine \"%s\" : %s" % (name, err.errorLabel))
    except Exception as err:
      self.exitError("Failed to deprovision engine VM \"%s\": %s" % (name, err))
