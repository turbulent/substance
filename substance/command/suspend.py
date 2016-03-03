from substance.command import Command
from substance.exceptions import (SubstanceError)

class Suspend(Command):
  def main(self):
    name = self.args[0]

    try:
      engine = self.core.getEngine(name)
      engine.readConfig()
      engine.suspend()
    except SubstanceError as err:
      self.exitError(err.errorLabel)
    except Exception as err:
      self.exitError("Failed to suspend engine \"%s\": %s" % (name, err))
