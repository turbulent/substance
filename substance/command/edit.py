import os
import logging
from substance.logs import *
from substance.monads import *
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (EngineNotFoundError)

class Edit(Command):

  def main(self):

    name = self.getInputName()
 
    self.core.loadEngine(name) \
      .bind(self.editEngineConfig) \
      .catch(self.exitError) 


  def editEngineConfig(self, engine):
    cmd = os.environ.get('EDITOR', 'vi') + ' ' + engine.config.getConfigFile()
    return Shell.call(cmd) 
