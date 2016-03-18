import logging
from substance.command import Command
from substance.monads import *

class Testcom(Command):

  vboxManager = None
  vbox = None

  def getShellOptions(self, optparser):
    optparser.add_option("-v", dest="val", help="Single Val", default=False)
    optparser.add_option("--longval", dest="longval", help="Long Val", default=False)
    optparser.add_option("-b", dest="bool", help="Boolean", default=False, action="store_true")
    optparser.add_option("--longbool", dest="longbool", help="Long Boolean", default=False, action="store_true")
    return optparser

  def main(self):
    logging.info("Test command!")
    logging.debug("Input: %s", self.input)
    logging.debug("Options: %s", self.options)
    logging.debug("Args: %s", self.args)

