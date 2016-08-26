from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Launch(Command):

  def getUsage(self):
    return "substance launch"
   
  def getHelpTitle(self):
    return "Launch the current engine's virtual machine"

  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    return optparser

  def main(self):

    return self.core.readCurrentEngineName() \
      .bind(self.core.loadEngine) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.launch) \
      .catch(self.exitError)
