from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Ssh(Command):

  def getUsage(self):
    return "substance ssh [container?]"
  
  def getHelpTitle(self):
    return "Connect using SSH to the engine or directly into a container"

  def getShellOptions(self, optparser):
    optparser.add_option("-u", "--user", dest="user", help="User to connect", default=None)
    optparser.add_option("-d", "--cwd", dest="cwd", help="Change to this directory upon connect", default=None)
    return optparser

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envShell, container=self.getInputContainer(), user=self.getOption('user'), cwd=self.getOption('cwd')) \
      .catch(self.exitError)

  def getInputContainer(self):
    if len(self.args) <= 0:
      return None
    return self.args[0]
