# -*- coding: utf-8 -*-
# $Id$

import traceback
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (SubstanceError)

class Deprovision(Command):
  def main(self):
    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      if not self.core.getConfigKey('assumeYes') and not Shell.printConfirm("You are about to deprovision engine VM \"%s\"." % name):
        self.exitOK("User cancelled.")

      engine.readConfig()
      engine.deprovision()

    except SubstanceError as err:
      self.exitError(err.errorLabel)
    except Exception as err:
      self.exitError(traceback.format_exc() + "Failed to deprovision engine \"%s\": %s" % (name, err))
