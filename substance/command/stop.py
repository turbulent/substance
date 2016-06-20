from substance.monads import *
from substance.logs import *
from substance import (Command, Shell, Engine)

class Stop(Command):

  def getUsage(self):
    return "substance stop [ENGINE NAME]"

  def getHelpTitle(self):
    return "Stop an engine's vm gracefully or forcefully."

  def getShellOptions(self, optparser):
    optparser.add_option("-f", "--force", dest="force", help="Force power off", action="store_true")
    return optparser

  def main(self):

    name = self.getInputName()

    forced = self.options.force
    #if forced and  not Shell.printConfirm("You are about to force stop engine \"%s\"." % name):
    #  self.exitOK("User cancelled.")

    self.core.initialize() \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(defer(Engine.stop, force=forced)) \
      .catch(self.exitError)
