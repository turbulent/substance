import logging
from substance.command import Command
from substance.shell import Shell

class Testcom(Command):
  def getShellOptions(self, optparser):
    optparser.add_option("-v", dest="val", help="Single Val", default=False)
    optparser.add_option("--longval", dest="longval", help="Long Val", default=False)
    optparser.add_option("-b", dest="bool", help="Boolean", default=False, action="store_true")
    optparser.add_option("--longbool", dest="longbool", help="Long Boolean", default=False, action="store_true")
    return optparser
 
  def main(self):
    logging.info("Test command!")
    logging.debug("Input: %s" % self.input)
    logging.debug("Options: %s" % self.options)
    logging.debug("Args: %s" % self.args)

    try:
      self.core.assertPaths()
    except Exception as err:
      self.exitError(err)
      
    logging.debug("Config: %s" % self.core.getConfig())

    engines = self.core.getEngines()
    logging.debug("Engines: %s" % engines)
    for name in engines:
      engine = self.core.getEngine(name)
      logging.debug( "Engine %s: %s" % (engine.getName(), engine))
      config = engine.readConfig()
      logging.debug("  Config: %s" % (config) )
