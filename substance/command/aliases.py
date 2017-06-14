from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Aliases(Command):

  def getUsage(self):
    return "substance aliases [opts]"
  
  def getHelpTitle(self):
    return "Execute a command within a container"

  def getShellOptions(self, optparser):
    optparser.add_option("-p","--prefix", dest="prefix", help="Prefix of aliases", default="")
    optparser.add_option("-s","--suffix", dest="suffix", help="Suffix of aliases", default="")
    return optparser

  def main(self):
    return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
      .bind(Engine.loadConfigFile) \
      .bind(self.exportAliases) \
      .catch(self.exitError)
  
  def exportAliases(self, engine):
    aliases = engine.config.get('aliases')
    if aliases:
      prefix = self.getOption('prefix')
      suffix = self.getOption('suffix')
      exports = [ "alias %s%s%s=\"substance -e %s %s\"" % (prefix,alias,suffix,engine.name,alias) for alias in aliases.keys() ]
      print "\n".join(exports)
      return OK(True)
    else:
      return Fail("Engine %s has no aliases." % engine.name)

