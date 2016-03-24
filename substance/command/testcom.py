import logging
from substance.command import Command
from substance.engine import Engine
from substance.monads import *
from substance.logs import *

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

    name = self.getInputName()

    self.core.initialize()  \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.printEngineInfo)  \
      .bind(self.printForwardedPorts)  \
      .catch(self.exitError)


  def printEngineInfo(self, engine):

    driver = engine.getDriver()
    machInfo = driver.getMachineInfo(engine.getDriverID()).catch(self.exitError).getOK()

    for k,v in machInfo.iteritems():
      print("%s = %s" % (k,v))

    return OK(engine) 

  def printForwardedPorts(self, engine):

    driver = engine.getDriver()
    ports = driver.fetchForwardedPorts(engine.getDriverID()) \
      .catch(self.exitError).getOK()

    for port in ports:
      print("Forwarded Port(%(name)s) NIC:%(nic)s, hostIP: %(hostIP)s, hostPort: %(hostPort)s, guestIP: %(guestIP)s, guestPort: %(guestPort)s" % port)

    return OK(ports) 
