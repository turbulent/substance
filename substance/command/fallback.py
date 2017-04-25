from substance import (Engine, Command)
from substance.exceptions import (LinkCommandError)

class Fallback(Command):

  def getUsage(self):
    return ""

  def getHelpTitle(self):
    return ""

  def getShellOptions(self, optparser):
    return optparser

  # Disable parsing for this command
  def execute(self, args=None):
    self.input = args
    self.args = args

    self.main()

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.envExecAlias, alias=self.name, args=self.args) \
      .catch(self.onEngineException)

  def onEngineException(self, err):
    if isinstance(err, LinkCommandError):
      # Hide message, forward status code instead
      return self.exitError(None, code=err.code)
    return self.exitError(err)
