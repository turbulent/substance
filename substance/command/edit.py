import os
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (EngineNotFoundError)

class Edit(Command):

  def main(self):
    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      cmd = os.environ.get('EDITOR', 'vi') + ' ' + engine.configFile
      Shell.call(cmd)

    except EngineNotFoundError:
      self.exitError("Engine \"%s\" does not exist" % name)
