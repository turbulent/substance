# -*- coding: utf-8 -*-
# $Id$

import traceback
from substance.logs import *
from substance.monads import *
from substance.engine import Engine
from substance.command import Command
from substance.shell import Shell
from substance.exceptions import (SubstanceError)

class Deprovision(Command):
  def main(self):
    name = self.getInputName()
  
    # XXX Add confirm check
 
    self.core.initialize() \
      .then(defer(self.ask, "You are about to deprovision engine \"%s\"" % name)) \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.deprovision) \
      .catch(self.exitError)
