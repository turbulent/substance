from substance import (Command, Engine)
from substance.logs import (logging)

logger = logging.getLogger(__name__)

class Expose(Command):

  def getUsage(self):
    return "substance expose [options] LOCALPORT[:PUBLICPORT]"

  def getHelpTitle(self):
    return "Expose an engine port as a port on the host machine."

  def getShellOptions(self, optparser):
    optparser.add_option(
      "-s",
      "--scheme",
      dest="scheme",
      help="Specify the uri scheme (e.g. wss) that this port will be used for.",
      default=None)
    return optparser

  def main(self):
    portdef = self.getArg(0)
    if not portdef:
      return self.exitHelp("You must provide a port description!")

    if ":" in portdef:
      (loc, pub) = portdef.split(":", 2)
      local_port = int(loc)
      public_port = int(pub)
    else:
      local_port = int(portdef)
      public_port = int(portdef)

    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.exposePort, local_port, public_port, self.getScheme(public_port))

  def getScheme(self, public_port):
    scheme = self.getOption('scheme')
    if scheme:
      return scheme
    # Try a guess!
    return {
      20: "ftp",
      21: "ftp",
      22: "ssh",
      23: "telnet",
      25: "smtp",
      53: "dns",
      70: "gopher", # Yeah that's right. Long live Gopher!
      79: "finger",
      80: "http",
      123: "ntp",
      143: "imap",
      161: "snmp",
      162: "snmp",
      194: "irc",
      199: "snmp",
      220: "imap",
      443: "https",
      445: "smb",
      465: "smtp",
      873: "rsync",
      944: "nfs",
      992: "telnet",
      994: "ircs",
      8080: "http",
      6660: "irc",
      6661: "irc",
      6662: "irc",
      6663: "irc",
      6664: "irc",
      6665: "irc",
      6666: "irc",
      6667: "irc",
      6668: "irc",
      6669: "irc"
    }.get(public_port, "ws")
