from substance.monads import *
from substance.logs import *
from substance.engine import Engine
from substance.command import Command
from substance.exceptions import (SubstanceError)

class Guestadd(Command):

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.viewGuestAdditions) \
      .catch(self.exitError)

  def viewGuestAdditions(self, engine):
    op = engine.getDriver().fetchGuestAddVersion(engine.getDriverID())
    if op.isFail():
      return op

    logging.info("Guest Additions: %s" % op.getOK()) 
    return OK(engine)
