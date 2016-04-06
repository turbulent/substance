import logging
from substance.command import Command
from substance.engine import Engine
from substance.monads import *
from substance.logs import *
from substance.link import Link
from substance.box import Box
from pkg_resources import Requirement, resource_filename
import paramiko

from substance.driver.virtualbox.machine import *
from substance.driver.virtualbox.network import *

class Boxtest(Command):

  vboxManager = None
  vbox = None

  def getShellOptions(self, optparser):
    optparser.add_option("-v", dest="val", help="Single Val", default=False)
    optparser.add_option("--longval", dest="longval", help="Long Val", default=False)
    optparser.add_option("-b", dest="bool", help="Boolean", default=False, action="store_true")
    optparser.add_option("--longbool", dest="longbool", help="Long Boolean", default=False, action="store_true")
    return optparser

  def main(self):

    name = self.getBoxArg()

    self.core.initialize()  \
      .then(defer(self.core.readBox, boxstring=name)) \
      .bind(defer(Box.fetch)) \
      .catch(self.exitError)


  def getBoxArg(self):
    if len(self.args) <= 0:
      return self.exitError("Please specify a box.")
    return self.args[0]

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
