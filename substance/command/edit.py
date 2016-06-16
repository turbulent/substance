import os
import logging
from substance.logs import *
from substance.monads import *
from substance import (Engine, Command, Shell)
from substance.exceptions import (EngineNotFoundError)

class Edit(Command):

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name=name)) \
      .bind(self.editEngineConfig) \
      .bind(Engine.loadConfigFile) \
      .then(dinfo("Engine \"%s\" configuration was updated.", name)) \
      .catch(self.exitError) 

  def editEngineConfig(self, engine):
    cmd = os.environ.get('EDITOR', 'vi') + ' ' + engine.config.getConfigFile()
    return Shell.call(cmd).map(lambda x: engine)
