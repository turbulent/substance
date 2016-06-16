import logging
from substance import (Command, Engine, Link)
from substance.monads import *
from substance.logs import *

class Connect(Command):

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

    name = self.getInputName()

    self.core.initialize()  \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.testConnect) \
      .bind(self.runRemoteCommand) \
      .catch(self.exitError)

  def testConnect(self, engine):
    logging.info("Connecting to engine \"%s\"..." % engine.name)
    keyFile = resource_filename(Requirement.parse("substance"), "support/substance_insecure")
    link = Link(keyFile=keyFile)
    return link.connectEngine(engine)

  def runRemoteCommand(self, link):
    return link.command("w") \
      .bind(self.printLinkResponse) \
      .then(defer(link.command, cmd="ls -al")) \
      .bind(self.printLinkResponse) \
      .then(defer(link.command, cmd="unknowncommandshouldfail")) \
      .bind(self.printLinkResponse)  \
      .then(defer(link.upload, '/tmp/testSource', 'testSource')) \
      .then(defer(link.download, 'testSource', '/tmp/testDest'))  \
      .then(defer(link.command, cmd="ls -al")) \
      .bind(self.printLinkResponse) \

  def printLinkResponse(self, lr):
    logging.info("Command: %s" % lr.cmd)
    logging.info("Return code: %s" % lr.code)
    logging.info("%s" % lr.stdout.read())   
    logging.info("%s" % lr.stderr.read())   
    return OK(lr.link) 
