import os
import logging
from substance.logs import *
from substance.monads import *
from substance.engine import Engine
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (EngineNotFoundError)

class Edit(Command):

  def main(self):

    name = self.getInputName()
 
    self.core.loadEngine(name) \
      .bind(self.editEngineConfig) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.validateConfig) \
      .then(dinfo("Engine \"%s\" configuration is valid.", name)) \
      .catch(self.exitError) 

  def editEngineConfig(self, engine):
    cmd = os.environ.get('EDITOR', 'vi') + ' ' + engine.config.getConfigFile()
    return Shell.call(cmd).map(lambda x: engine)
