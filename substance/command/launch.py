# -*- coding: utf-8 -*-
# $Id$

import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( 
  EngineNotFoundError, 
  EngineAlreadyRunning, 
  SubstanceDriverError 
)

class Launch(Command):

  def getShellOptions(self, optparser):
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)
      engine.readConfig()
      engine.launch()

    except EngineNotFoundError as err:
      self.exitError(err.errorLabel)
    except EngineAlreadyRunning as err:
      self.exitOK(err.errorLabel)
    except Exception as err:
      self.exitError("Failed to launch engine VM \"%s\": %s" % (name, err))
