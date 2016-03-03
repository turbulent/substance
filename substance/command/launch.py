from substance.command import Command
from substance.exceptions import (SubstanceError)

class Launch(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    name = self.args[0]

    try:
      engine = self.core.getEngine(name)
      engine.readConfig()
      engine.launch()

    except SubstanceError as err:
      self.exitError(err.errorLabel)
    except Exception as err:
      self.exitError("Failed to launch engine \"%s\": %s" % (name, err))
