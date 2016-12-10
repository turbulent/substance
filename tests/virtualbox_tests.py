import unittest
import os
import tempfile
import tests
import re
from substance.core import Core
from substance.engine import (EngineProfile, Engine)
from substance.shell import Shell
from substance.monads import *
from substance.constants import *

import substance.driver.virtualbox.vbox as vbox
import substance.driver.virtualbox.machine as machine
import substance.driver.virtualbox.network as network

class TestVirtualBox(tests.TestBase):

  core = None
  engine = None
  basePath = None
  projectsPath = None

  vmTest = True
  vmName = "testVbox"
  vmUUID = None

  @classmethod
  def setUpClass(cls):
    cls.basePath = cls.addTemporaryDir()
    cls.projectsPath = cls.addTemporaryDir()


  @classmethod
  def tearDownClass(cls):
    if cls.vmUUID:
      machine.terminate(cls.vmUUID)
      machine.delete(cls.vmUUID)

    if cls.basePath:
      Shell.nukeDirectory(cls.basePath).catch(cls.raiser)
    if cls.projectsPath:
      Shell.nukeDirectory(cls.projectsPath).catch(cls.raiser)

  def testReadVersion(self):
    op = vbox.readVersion()
    self.assertIsInstance(op, OK)
    self.assertTrue(re.match(r'^[0-9\.]*$', op.getOK()))

  def testReadDHCPs(self):
    op = network.readDHCPs()
    self.assertIsInstance(op, OK)
   
    dhcps = op.getOK()
    self.assertEqual(type(dhcps), type([]))

    for dhcp in dhcps:
      self.assertIsInstance(dhcp, network.DHCP)

  def testHostOnlyOperations(self):
    op = network.readHostOnlyInterfaces()
    self.assertIsInstance(op, OK)

    hoifs = op.getOK()
    self.assertEqual(type(hoifs), type([]))
    for hoif in hoifs:
      self.assertIsInstance(hoif, network.HostOnlyInterface)

    op = network.addHostOnlyInterface()
    self.assertIsInstance(op, OK)
    iface = op.getOK()

    options = {'ip':'10.0.123.1', 'netmask':'255.255.255.0'}
    op = network.configureHostOnlyInterface(iface, **options)
    self.assertIsInstance(op, OK)
    
    op = network.readHostOnlyInterface(iface)
    hoif = op.getOK()
    self.assertIsInstance(op, OK)
    self.assertIsInstance(hoif, network.HostOnlyInterface)
    self.assertEqual(hoif.name, iface)
    self.assertEqual(hoif.network.v4ip.format(), options['ip'])
    self.assertEqual(hoif.network.v4mask.format(), options['netmask'])

    dhcpOptions = {'gateway':'10.0.123.1', 'netmask':'255.255.255.0', 'lowerIP':'10.0.123.1', 'upperIP':'10.0.123.100'}   
    op = network.addDHCP(iface, **dhcpOptions)
    self.assertIsInstance(op, OK)

    op = network.readDHCP(iface)
    self.assertIsInstance(op, OK)
    dhcp = op.getOK()
    self.assertIsInstance(dhcp, network.DHCP)
    self.assertEqual(dhcp.interface, iface)
    self.assertEqual(dhcp.gateway, dhcpOptions['gateway']) 
    self.assertEqual(dhcp.netmask, dhcpOptions['netmask']) 
    self.assertEqual(dhcp.lowerIP, dhcpOptions['lowerIP']) 
    self.assertEqual(dhcp.upperIP, dhcpOptions['upperIP']) 

    op = network.removeHostOnlyInterface(hoif)
    self.assertIsInstance(op, OK)
    op = network.readHostOnlyInterface(iface)
    self.assertIsInstance(op, Fail)
    op = network.readDHCP(iface)
    self.assertIsInstance(op, Fail)

  def testReadMachines(self):
    op = machine.readMachines()
    self.assertIsInstance(op, OK)
    self.assertIsInstance(op.getOK(), dict)
    
  def testSequence(self):
    if not self.vmTest:
      return

    self.doImport()
    self.doTestPF()
    self.doTestSF()
    self.doReadGuestAdd()
    self.doStart()
    self.doSuspend()
    self.doStart()
    self.doTerminate()
    self.doDelete()

  def testDHCP(self):
    dhcpA = network.DHCP(1, "host", "192.168.1.1", "255.255.255.0", "192.168.1.10", "192.168.1.20", True)
    dhcpB = network.DHCP(2, "priv", "172.16.1.1", "255.255.255.0", "172.16.1.10", "172.16.1.20", True)
    dhcpC = network.DHCP(3, "long", "10.0.1.1", "255.255.255.0", "10.0.1.10", "10.0.1.20", True)
    sdhcpA = network.DHCP(1, "host", "192.168.1.1", "255.255.255.0", "192.168.1.10", "192.168.1.20", True)
    sdhcpB = network.DHCP(2, "priv", "172.16.1.1", "255.255.255.0", "172.16.1.10", "172.16.1.20", True)
    sdhcpC = network.DHCP(3, "long", "10.0.1.1", "255.255.255.0", "10.0.1.10", "10.0.1.20", True)
    dhcps = [dhcpA,dhcpB,dhcpC]
    sdhcps = [sdhcpA,sdhcpB,sdhcpC]

    self.assertEqual(dhcpA,sdhcpA)
    self.assertEqual(dhcpB,sdhcpB)
    self.assertEqual(dhcpC,sdhcpC)
    self.assertIn(sdhcpA,dhcps) 
    self.assertIn(sdhcpB,dhcps) 
    self.assertIn(sdhcpC,dhcps) 
    self.assertIn(dhcpA,sdhcps) 
    self.assertIn(dhcpB,sdhcps) 
    self.assertIn(dhcpC,sdhcps) 
  
  def testHOIFs(self):
    h1 = network.HostOnlyInterface("nic1", "00:00:00:00:00:00", "192.168.1.10", "255.255.255.0", None, None, "Up", "host")
    h2 = network.HostOnlyInterface("nic2", "0f:00:00:00:00:00", "192.168.1.11", "255.255.255.0", None, None, "Up", "host")
    h3 = network.HostOnlyInterface("nic3", "0g:00:00:00:00:00", "192.168.1.12", "255.255.255.0", None, None, "Up", "host")
    sh1 = network.HostOnlyInterface("nic1", "00:00:00:00:00:00", "192.168.1.10", "255.255.255.0", None, None, "Up","host")
    sh2 = network.HostOnlyInterface("nic2", "0f:00:00:00:00:00", "192.168.1.11", "255.255.255.0", None, None, "Up", "host")
    sh3 = network.HostOnlyInterface("nic3", "0g:00:00:00:00:00", "192.168.1.12", "255.255.255.0", None, None, "Up", "host")
 
    hs = [h1,h2,h3] 
    shs = [sh1,sh2,sh3]
  
    self.assertEqual(h1, sh1) 
    self.assertEqual(h2, sh2) 
    self.assertEqual(h3, sh3) 
    self.assertIn(h1, shs)
    self.assertIn(h2, shs)
    self.assertIn(h3, shs)
    self.assertIn(sh1, hs)
    self.assertIn(sh2, hs)
    self.assertIn(sh3, hs)

  def testPort(self):
    portA = network.PortForward("test-ssh", 1, "tcp", "", "9866", "", "22")
    portB = network.PortForward("test-http", 1, "tcp", "", "9867", "", "80")
    portC = network.PortForward("test-https", 1, "tcp", "", "9868", "", "443")
    sportA = network.PortForward("test-ssh", 1, "tcp", "", "9866", "", "22")
    sportB = network.PortForward("test-http", 1, "tcp", "", "9867", "", "80")
    sportC = network.PortForward("test-https", 1, "tcp", "", "9868", "", "443")
    
    ports = [portA,portB,portC]
    sports = [sportA,sportB,sportC]
  
    self.assertTrue(portA == sportA)
    self.assertTrue(portB == sportB)
    self.assertTrue(portC == sportC)
    self.assertIn(portA, sports) 
    self.assertIn(portB, sports) 
    self.assertIn(portC, sports) 
    self.assertIn(sportA, ports) 
    self.assertIn(sportB, ports) 
    self.assertIn(sportC, ports) 
 
  def doImport(self):
    ovfFile = "/Users/bbeausej/dev/substance-engine/box.ovf"
    op = machine.inspectOVF(ovfFile) \
      .bind(defer(machine.makeImportParams, name=self.vmName)) \
      .bind(defer(machine.importOVF, ovfFile=ovfFile, name=self.vmName))
    self.assertIsInstance(op, OK)
    self.assertIsNotNone(op.getOK())

    type(self).vmUUID = op.getOK()

    op = machine.readMachineExists(self.vmUUID)
    self.assertIsInstance(op, OK)

    self.assertTrue(op.getOK())

  def doTestPF(self):
    portA = network.PortForward("test-ssh", 1, "tcp", "", "9866", "", "22")
    portB = network.PortForward("test-http", 1, "tcp", "", "9867", "", "80")
    portC = network.PortForward("test-https", 1, "tcp", "", "9868", "", "443")
    ports = [portA,portB,portC]

    op = network.addPortForwards(ports, self.vmUUID)  \
      .then(defer(network.readPortForwards, uuid=self.vmUUID))
    self.assertIsInstance(op, OK)
    
    setports = op.getOK()
    self.assertEqual(type(setports), type([]))

    for port in setports:
      self.assertIsInstance(port, network.PortForward)

    for port in ports:
      self.assertIn(port, setports)

    op = network.removePortForwards([portB], self.vmUUID) \
      .then(defer(network.readPortForwards, uuid=self.vmUUID))
    self.assertIsInstance(op, OK)
 
    self.assertIn(portA, op.getOK())
    self.assertNotIn(portB, op.getOK())
    self.assertIn(portC, op.getOK())

    op = network.clearPortForwards(self.vmUUID) \
      .then(defer(network.readPortForwards, uuid=self.vmUUID))

    self.assertIsInstance(op, OK)
    self.assertEqual(op.getOK(), [])

  def doTestSF(self):
    d1 = self.addTemporaryDir()
    f1 = machine.SharedFolder(os.path.basename(d1), d1)
    d2 = self.addTemporaryDir()
    f2 = machine.SharedFolder(os.path.basename(d2), d2)
    folders = [f1, f2]

    op = machine.addSharedFolders(folders, self.vmUUID) \
      .then(defer(machine.readSharedFolders, uuid=self.vmUUID))
    self.assertIsInstance(op, OK)
    self.assertEqual(len(op.getOK()), 2)
    self.assertEqual([ x.hostPath for x in op.getOK() ], [d1, d2])
   
    op = machine.clearSharedFolders(self.vmUUID) \
      .then(defer(machine.readSharedFolders, uuid=self.vmUUID))
    self.assertIsInstance(op, OK)
    self.assertEqual(len(op.getOK()), 0)


  def doStart(self):
    self.assertIsInstance(machine.start(self.vmUUID), OK)
    self.checkStateMatch("running")

  def doSuspend(self):
    self.assertIsInstance(machine.suspend(self.vmUUID), OK)
    self.checkStateMatch("saved")

  def doTerminate(self):
    self.assertIsInstance(machine.terminate(self.vmUUID), OK)
    self.checkStateMatch("poweroff")

  def doDelete(self):
    self.assertIsInstance(machine.delete(self.vmUUID), OK)
    op = machine.readMachineExists(self.vmUUID)
    self.assertIsInstance(op, OK)
    self.assertFalse(op.getOK())
    type(self).vmUUID = None

  def checkStateMatch(self, stateMatch):
    state = machine.readMachineState(self.vmUUID)
    self.assertIsInstance(state, OK)
    self.assertEqual(state.getOK(), stateMatch)

  def doReadGuestAdd(self):
    op = machine.readGuestAddVersion(self.vmUUID)
    self.assertIsInstance(op, OK)
    self.assertTrue(re.match(r'^[0-9\.]*$', op.getOK()))

