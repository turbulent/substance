import logging
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (SubstanceError)

class Delete(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)
      engine.readConfig()

      if not self.core.getConfigKey('assumeYes') and not Shell.printConfirm("You are about to delete engine \"%s\"." % name):
        self.exitOK("User cancelled.")

      if engine.isProvisioned():
        engine.deprovision()
        logging.info("Engine \"%s\" has been deprovisioned.", name)

      self.core.removeEngine(name)
      logging.info("Engine \"%s\" has been deleted.", name)

    except SubstanceError as err:
      self.exitError(err.errorLabel)
    except Exception as err:
      self.exitError("Failed to deprovision engine VM \"%s\": %s" % (name, err))
