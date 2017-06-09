from __future__ import absolute_import
import os
import logging
from collections import OrderedDict
from substance.logs import *
from substance.monads import *
from substance.config import Config
from substance.driver import Driver
from substance.constants import (EngineStates)
from substance.exceptions import (FileDoesNotExist)

from .vbox import (vboxManager)
from . import network
from . import machine
from .exceptions import *

from netaddr import (IPAddress, IPNetwork)
from functools import reduce

logger = logging.getLogger(__name__)

class VirtualBoxDriver(Driver):
  '''
  Substance VirtualBox driver class. Interface to virtual box manager.
  '''

  def __init__(self, core):
    super(self.__class__, self).__init__(core)
    self.config = Config(os.path.join(self.core.getBasePath(), "virtualbox.yml"))

  def assertSetup(self):
    return self.assertConfig().then(self.assertNetworking)

  # -- Configuration

  def getDefaultConfig(self):
    defaults = OrderedDict()
    defaults['network'] = "172.21.21.0/24"
    defaults['interface'] = None
    return defaults

  def makeDefaultConfig(self):
    self.logAdapter.info("Generating default virtualbox config in %s" % self.config.getConfigFile())
    defaults = self.getDefaultConfig()
    for kkk, vvv in defaults.items():
      self.config.set(kkk, vvv)
    return self.config.saveConfig()

  def assertConfig(self):
    return self.config.loadConfigFile() \
      .catchError(FileDoesNotExist, lambda err: self.makeDefaultConfig())
 
  #---- Networking setup
 
  def getNetworkInterface(self):
    return self.config.get('interface', None)

  def readNetworkConfig(self): 
    netrange = IPNetwork(self.config.get('network'))
    netconfig = {
      'gateway': netrange[1].format(),
      'netmask': netrange.netmask.format(),
      'lowerIP': netrange[2].format(),
      'upperIP': netrange[-2].format()
    }

    return OK(netconfig)

  def assertNetworking(self):
    interface = self.getNetworkInterface()
    netconfig = self.readNetworkConfig()

    if interface:
      hoif = network.readHostOnlyInterface(interface) \
        .catchError(VirtualBoxObjectNotFound, lambda err: OK(None))
      dhcp = network.readDHCP(interface) \
        .catchError(VirtualBoxObjectNotFound, lambda err: OK(None))
  
      return Try.sequence((netconfig, hoif, dhcp)) \
        .bind(self.assertNetworkConfiguration)
    else:
      return netconfig.bind(self.provisionNetworking)
 
  def assertNetworkConfiguration(self, netparts):

    (netconfig, hoif, dhcp) = netparts

    if not hoif:
      return self.provisionNetworking(netconfig)
    elif hoif.v4ip.format() != netconfig['gateway']:
      self.logAdapter.warning("VirtualBox interface \"%s\" is not properly configured. Creating a new host-only network." % hoif.name)
      return self.provisionNetworking(netconfig)
    elif dhcp is None:
      self.logAdapter.warning("VirtualBox interface \"%s\" does not have DHCP enabled. Re-Establishing now." % hoif.name)
      return self.provisionDHCP(hoif.name, netconfig)

    return OK(hoif)
 
  def provisionNetworking(self, netconfig):
    self.logAdapter.info("Provisioning VirtualBox networking for substance")
    ifm = network.addHostOnlyInterface() 
    if ifm.isFail():
      return ifm
    iface = ifm.getOK()

    return network.configureHostOnlyInterface(iface, ip=netconfig['gateway'], netmask=netconfig['netmask']) \
      .then(defer(self.provisionDHCP, interface=iface, netconfig=netconfig)) \
      .then(defer(self.saveInterface, iface=iface)) \
      .then(defer(network.readHostOnlyInterface, name=iface))

  def provisionDHCP(self, interface, netconfig):
    self.logAdapter.info("Provisioning DHCP service for host only interface")
    network.removeDHCP(interface).catch(lambda x: OK(interface)) \
      .bind(defer(network.addDHCP, **netconfig))

  def saveInterface(self, iface):
    self.config.set('interface', iface)
    return self.config.saveConfig()

  #---- Machine API
  
  def importMachine(self, name, ovfFile, engineProfile=None):
    return self.assertSetup() \
      .then(defer(machine.inspectOVF, ovfFile)) \
      .bind(defer(machine.makeImportParams, name=name, engineProfile=engineProfile)) \
      .bind(defer(machine.importOVF, ovfFile=ovfFile, name=name))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    state = machine.readMachineState(uuid)
    if state.isFail():
      return state

    if state.getOK() in [machine.MachineStates.PAUSED]:
      return machine.resume(uuid)
    else:
      return machine.start(uuid) 

  def readMachineWaitForNetwork(self, uuid, timeout=5000):
    return machine.readWaitGuestProperty(uuid, "/VirtualBox/GuestInfo/Net", timeout)

  def readMachineNetworkInfo(self, uuid):
    def format(res):
      info = OrderedDict()
      info['sshPort'] = res[0].hostPort if res[0] else None
      info['sshIP'] = '127.0.0.1'
      info['privateIP'] = res[1]
      info['publicIP'] = res[2]
      return info

    return Try.sequence([
      network.readPortForward(uuid, name="substance-ssh"),
      machine.readGuestProperty(uuid, "/VirtualBox/GuestInfo/Net/0/V4/IP"),
      machine.readGuestProperty(uuid, "/VirtualBox/GuestInfo/Net/1/V4/IP")
    ]).map(format)

  def configureMachine(self, uuid, engine):
   
    def engineFolderToVBoxFolder(acc, x):
      if x.mode == 'sharedfolder':
        acc.append(machine.SharedFolder(name=x.name, hostPath=x.hostPath))
      return acc

    folders = reduce(engineFolderToVBoxFolder, engine.getEngineFolders(), [])
    desiredPort = engine.getSSHPort()

    return self.assertSetup() \
      .then(defer(self.resolvePortConflict, uuid=uuid, desiredPort=desiredPort)) \
      .then(defer(self.configureMachineAdapters, uuid=uuid)) \
      .then(defer(self.configureMachineFolders, uuid=uuid, folders=folders)) \
      .then(defer(self.configureMachineProfile, uuid=uuid, engine=engine))

  def configureMachineProfile(self, uuid, engine):
    self.logAdapter.info("Configure machine profile")
    profile = engine.getProfile()
    return machine.configureProfile(uuid, profile.cpus, profile.memory)

  def configureMachineFolders(self, folders, uuid):
    self.logAdapter.info("Configure machine shared folders")
    return machine.clearSharedFolders(uuid) \
      .then(defer(machine.addSharedFolders, folders=folders, uuid=uuid))

  def resolvePortConflict(self, uuid, desiredPort):
    self.logAdapter.info("Checking for port conflicts")
    return network.readAllPortForwards(ignoreUUIDs=[uuid]) \
      .bind(defer(self.determinePort, desiredPort=desiredPort)) \
      .bind(defer(self.configurePort, uuid=uuid))
       
  def determinePort(self, usedPorts, desiredPort):
    basePort = 4500
    self.logAdapter.debug("Base port: %s" % basePort) 
    self.logAdapter.debug("Desired port: %s" % desiredPort)
    unavailable = [x.hostPort for x in usedPorts]
    port = desiredPort if desiredPort >= basePort else basePort
    while port in unavailable or port < basePort:
      self.logAdapter.debug("Port %s is in use." % port)
      port += 1
    self.logAdapter.info("Determined SSH port as %s" % port)
    return OK(port)

  def configurePort(self, port, uuid):
    self.logAdapter.debug("Configure substance-ssh port on port %s" % port)
    pf = network.PortForward("substance-ssh", 1, "tcp", None, port, None, 22)
    return network.removePortForwards([pf], uuid) \
      .catch(lambda err: OK(None)) \
      .then(defer(network.addPortForwards, [pf], uuid))

  def configureMachineAdapters(self, uuid):
    interface = self.getNetworkInterface()
    adapters = [ 
      machine.AdapterSettings(machine.AdapterTypes.NAT, 'default', None, False),
      machine.AdapterSettings(machine.AdapterTypes.HOSTONLY, interface, None, False),
      machine.AdapterSettings(machine.AdapterTypes.NONE, None, None, False),
      machine.AdapterSettings(machine.AdapterTypes.NONE, None, None, False)
    ]
    return Try.sequence([machine.configureAdapter(uuid, i+1, x) for i, x in enumerate(adapters)])

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    return machine.suspend(uuid)

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    return machine.halt(uuid)
    
  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    return machine.terminate(uuid)

  def deleteMachine(self, uuid):
    '''
    Delete the machine by driver identifier.
    '''
    return machine.delete(uuid)

  def exportMachine(self, uuid):
    #XXX To be implemented
    pass
 
  def getMachines(self):
    '''
    Retrieve the list of machines and their driver identifiers.
    '''
    return machine.readMachines()

  # -- Parse results from Virtual Box

  def getMachineID(self, name):
    '''
    Retrieve the driver specific machine ID for a machine name.
    '''
    return machine.findMachineID(name)

  def exists(self, uuid):
    '''
    Check in the driver that the specified identifier exists.
    '''
    return machine.readMachineExists(uuid)

  def isRunning(self, uuid):
    if self.getMachineState(uuid) is EngineStates.RUNNING:
      return True

  def isStopped(self, uuid):
    if self.getMachineState(uuid) is not EngineStates.RUNNING:
      return True

  def isSuspended(self, uuid):
    if self.getMachineState(uuid) is EngineStates.SUSPENDED:
      return True

  def getMachineState(self, uuid):
    '''
    Retrieve the Substance machine state for this driver id
    '''
    return machine.readMachineState(uuid) \
      .bind(self.machineStateToEngineState)

  def machineStateToEngineState(self, vboxState):
    '''
    Resolve a vbox machine state to a substance engine state.
    '''

    mapping = {
      machine.MachineStates.POWEROFF: EngineStates.STOPPED,
      machine.MachineStates.SAVED: EngineStates.SUSPENDED,
      machine.MachineStates.PAUSED: EngineStates.SUSPENDED,
      machine.MachineStates.ABORTED: EngineStates.STOPPED,
      machine.MachineStates.STUCK: EngineStates.STOPPED,
      machine.MachineStates.RESTORING: EngineStates.STOPPED,
      machine.MachineStates.SNAPSHOTTING: EngineStates.STOPPED,
      machine.MachineStates.SETTING_UP: EngineStates.STOPPED,
      machine.MachineStates.ONLINE_SNAPSHOTTING: EngineStates.STOPPED,
      machine.MachineStates.RESTORING_SNAPSHOT: EngineStates.STOPPED,
      machine.MachineStates.DELETING_SNAPSHOT: EngineStates.STOPPED,
      machine.MachineStates.LIVE_SNAPSHOTTING: EngineStates.RUNNING,
      machine.MachineStates.RUNNING: EngineStates.RUNNING,
      machine.MachineStates.STARTING: EngineStates.RUNNING,
      machine.MachineStates.STOPPING : EngineStates.RUNNING,
      machine.MachineStates.SAVING: EngineStates.RUNNING,
      machine.MachineStates.UNKNOWN: EngineStates.UNKNOWN,
      machine.MachineStates.INACCESSIBLE: EngineStates.INEXISTENT,
      machine.MachineStates.INEXISTENT: EngineStates.INEXISTENT
    }
    state = mapping.get(vboxState, EngineStates.UNKNOWN)
    ddebug("Machine state: %s : %s", vboxState, state)
    return OK(state)


