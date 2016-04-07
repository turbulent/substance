import os
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

class Runscript(Command):

  vboxManager = None
  vbox = None

  def getShellOptions(self, optparser):
    optparser.add_option("--sudo", dest="sudo", help="Run script with sudo", default=False, action="store_true")
    return optparser

  def main(self):

    name = self.getInputName()
    script = self.getArg()

    if not os.path.exists(script): 
      return self.exitError("Script file \"%s\" does not exist." % script)

    self.core.initialize()  \
      .then(defer(self.core.loadEngine, name=name)) \
      .bind(Engine.loadConfigFile) \
      .bind(defer(self.runScript, script=script, sudo=self.options.sudo)) \
      .bind(self.printLinkResponse) \
      .catch(self.exitError)

  def getArg(self):
    if len(self.args) < 2:
      return self.exitError("Please specify a script.")
    return self.args[1]

  def runScript(self, engine, script, sudo=False):
    link = engine.readLink() 
    if link.isFail():
      return link
    return link.getOK().runScript(script, sudo)

 
     
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
