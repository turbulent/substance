# -*- coding: utf-8 -*-
# $Id$

import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver

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
      
    (code, ip) = Shell.command("VBoxManage guestproperty get panic-test '/VirtualBox/GuestInfo/Net/0/V4/IP'")
    logging.info("IP: %s" %ip) 

    name = self.args[0]
   
    vbox = VirtualBoxDriver(baseFolder=self.core.getEnginesPath())
    uuid = vbox.getMachineID(name) 
    logging.info("Machine UUID for %s: %s" % (name, uuid))
