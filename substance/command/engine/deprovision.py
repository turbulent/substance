# -*- coding: utf-8 -*-
# $Id$

import traceback
from substance.logs import *
from substance.monads import *
from substance import (Engine, Command, Shell)
from substance.exceptions import (SubstanceError)

class Deprovision(Command):
  def getUsage(self):
    return "substance engine deprovision [ENGINE NAME]"

  def getHelpTitle(self):
    return "Destroy an engine's assocaited virtual machine"

  def main(self):
    name = self.getInputName()
    self.ask("You are about to deprovision engine \"%s\"" % name) \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.deprovision) \
      .catch(self.exitError)
