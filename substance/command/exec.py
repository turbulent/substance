from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)
import shlex

class Exec(Command):

  def getUsage(self):
    return "substance exec [opts] [CONTAINER] [CMD...]"
  
  def getHelpTitle(self):
    return "Execute a command within a container"

  def getShellOptions(self, optparser):
    optparser.add_option("-u", "--user", dest="user", help="User to connect", default=None)
    optparser.add_option("-d", "--cwd", dest="cwd", help="Change to this directory upon connect", default=None)
    return optparser

  # Disable intersped args 
  def execute(self, args=None):
    self.input = args
    (self.options, self.args) = self.parseShellInput(False)
   
    if len(self.args) == 0:
      return self.exitError("Please provider a container name to exec on.")

    self.container = self.args[0]
    self.main()


  def main(self):
    container = self.getInputContainer()
    if not container:
      return self.exitError("Please provide a container name to exec on.")

    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envExec, container=container, user=self.getOption('user'), cwd=self.getOption('cwd'), cmd=self.args[1:]) \
      .catch(self.exitError)

  def getInputContainer(self):
    if len(self.args) <= 0:
      return None
    return self.args[0]

