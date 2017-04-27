import subprocess
from substance import (Command, Engine)
from substance.logs import (logging)

logger = logging.getLogger(__name__)

class Expose(Command):

  def getUsage(self):
    return "substance expose [options] LOCALPORT[:PUBLICPORT]"

  def getHelpTitle(self):
    return "Expose an engine port as a port on the host machine."

  def main(self):
    portdef = self.getArg(0)
    if not portdef:
      return self.exitHelp("You must provide a port description!")

    if ":" in portdef:
      (local_port, public_port) = portdef.split(":", 2)
    else:
      local_port = portdef
      public_port = portdef

    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.exposePort, int(local_port), int(public_port))
