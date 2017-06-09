from __future__ import absolute_import
from builtins import next
from builtins import object
import re
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.constants import Constants
from .exceptions import *
from .vbox import (vboxManager, _vboxLineEnding)
from . import machine
from netaddr import (IPAddress, IPNetwork)

# -- Structs

class PortForward(object):
  def __init__(self, name, nic, proto, hostIP, hostPort, guestIP, guestPort):
    self.name = name
    self.nic = nic
    self.proto = proto
    self.hostIP = hostIP if hostIP else None
    self.hostPort = int(hostPort)
    self.guestIP = guestIP if guestIP else None
    self.guestPort = int(guestPort)

  def getCreateArg(self):
    return "--natpf%(nic)s \"%(name)s\",%(proto)s,%(hostIP)s,%(hostPort)s,%(guestIP)s,%(guestPort)s" % self.__dict__

  def getDeleteArg(self):
    return "--natpf%(nic)s delete \"%(name)s\"" % self.__dict__

  def __repr__(self):
    return "PortForward(%(nic)s, %(name)s, %(proto)s host(%(hostIP)s:%(hostPort)s) -> guest(%(guestIP)s:%(guestPort)s))" % self.__dict__

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__repr__() == other.__repr__()
    return False

 
class DHCP(object):
  def __init__(self, interface, networkName, gateway, netmask, lowerIP, upperIP, enabled):
    self.interface = interface
    self.networkName = networkName
    self.gateway = gateway
    self.netmask = netmask
    self.lowerIP = lowerIP
    self.upperIP = upperIP
    self.enabled = True if enabled == True or enabled == "Yes" else False

    self.network = IPNetwork(gateway+"/"+netmask)

  def __repr__(self):
    rep = "DHCP(%(interface)s gateway: %(gateway)s netmask %(netmask)s (%(lowerIP)s to %(upperIP)s))" % self.__dict__
    rep += " enabled" if self.enabled else ""
    return rep 

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__repr__() == other.__repr__()
    return False

class HostOnlyInterface(object):
  def __init__(self, name, mac=None, v4ip=None, v4mask=None, v6ip=None, v6prefix=None, status=None, netName=None):
    self.name = name
    self.mac = mac
    self.v4ip = v4ip
    self.v4mask = v4mask
    self.v6ip = v6ip
    self.v6prefix = v6prefix
    self.status = status
    self.netName = netName
    
 
    self.ip = IPAddress(v4ip)
    self.network = IPNetwork(v4ip+"/"+v4mask)

  def __repr__(self):
    return "HostOnlyInterface(%(name)s, %(mac)s IP: %(v4ip)s, netmask: %(v4mask)s, IPV6: %(v6ip)s, prefix: %(v6prefix)s status: %(status)s)" % self.__dict__
 
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__repr__() == other.__repr__()
    return False 

# -- Read funcs

def readAllPortForwards(ignoreUUIDs=[]):
  return machine.readMachines() \
    .mapM(lambda m: readPortForwards(m) if m not in ignoreUUIDs else OK([])) \
    .map(flatten)

def readPortForwards(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) >> parsePortForwards

def readPortForward(uuid, name=None):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    >> parsePortForwards \
    >> defer(filterPortForwards, name=name)
  
def readDHCPs():
  return vboxManager("list", "dhcpservers") \
    .bind(defer(_mapAsBlocks, func=parseDHCPBlock))

def readDHCP(interface):
  return readDHCPs() >> defer(filterDHCPs, interface=interface)

def readHostOnlyInterfaces():
  return vboxManager("list", "hostonlyifs") \
    .bind(defer(_mapAsBlocks, func=parseHostOnlyInterfaceBlock))

def readHostOnlyInterface(name):
  return readHostOnlyInterfaces() >> defer(filterHostOnlyInterfaces, name=name)

def filterPortForwards(ports, name):
  item = next((item for item in ports if item.name == name), None)
  return OK(item) if item else Fail(VirtualBoxObjectNotFound("Port Forward named \"%s\" was not found." % name))

def filterHostOnlyInterfaces(hoifs, name):
  item = next((item for item in hoifs if item.name == name), None)
  return OK(item) if item else Fail(VirtualBoxObjectNotFound("Host Only Interface \"%s\" was not found." % name))
  
def filterDHCPs(dhcps, interface):
  dhcp = next((dhcp for dhcp in dhcps if dhcp.interface == interface), None)
  return OK(dhcp) if dhcp else Fail(VirtualBoxObjectNotFound("DHCP for interface \"%s\" was not found." % interface))

# -- Parse funcs

def parseDHCPBlock(block):
  actions = (
    (r'^NetworkName:\s+HostInterfaceNetworking-(.+?)$', 'interface'),
    (r'^NetworkName:\s+(HostInterfaceNetworking-(.+?))$', 'networkName'),
    (r'^IP:\s+(.+?)$', 'gateway'),
    (r'^NetworkMask:\s+(.+?)$', 'netmask'),
    (r'^lowerIPAddress:\s+(.+?)$', 'lowerIP'),  
    (r'^upperIPAddress:\s+(.+?)$', 'upperIP'),  
    (r'Enabled:\s+(.+?)$', 'enabled')
  )
  return _extractClassFromBlock(block, actions, DHCP)


def parseHostOnlyInterfaceBlock(block):
  actions = (
    (r'^Name:\s+(.+?)$', 'name'),
    (r'^IPAddress:\s+(.+?)$', 'v4ip'),
    (r'^NetworkMask:\s+(.+?)$', 'v4mask'),
    (r'^IPV6Address:\s+(.+?)$', 'v6ip'),
    (r'^IPV6NetworkMaskPrefixLength:\s+(.+?)$', 'v6prefix'),
    (r'^Status:\s+(.+?)$', 'status'),
    (r'^VBoxNetworkName:\s+(.+?)$', 'netName'),
    (r'^HardwareAddress:\s+(.+?)$', 'mac'),
  )
  return _extractClassFromBlock(block, actions, HostOnlyInterface)
      
def parsePortForwards(vminfo):
  '''
  Parse Virtual Box machine info for forwarded ports.
  '''
  lines = vminfo.split(_vboxLineEnding())
  ports = []
  nic = None
  for line in lines:
    line = line.strip()

    # First match a nic from the info values
    nicmatch = re.match(r'^nic(\d+)=".+?"$', line)
    if nicmatch:
      nic = nicmatch.group(1)

    portmatch = re.match(r'^Forwarding.+?="(.+?),(.+?),(.*?),(.+?),(.*?),(.+?)"$', line)
    if portmatch:
      ports.append(PortForward(
        nic=nic,
        name=portmatch.group(1),
        proto=portmatch.group(2),
        hostIP=portmatch.group(3),
        hostPort=portmatch.group(4),
        guestIP=portmatch.group(5),
        guestPort=portmatch.group(6)
      ))

  return OK(ports)

# -- Actions

def clearPortForwards(uuid):
  return readPortForwards(uuid).bind(defer(removePortForwards, uuid=uuid))

def removePortForwards(ports, uuid):
  args = []
  for port in ports:
    args.append(port.getDeleteArg())
  
  if len(args) > 0: 
    return vboxManager("modifyvm", "\"%s\" %s" % (uuid, " ".join(args)))
  else:
    return OK(None)

def addPortForwards(ports, uuid):
  args = []
  for port in ports:
    args.append(port.getCreateArg())

  if len(args) > 0:
    return vboxManager("modifyvm", "\"%s\" %s" % (uuid, " ".join(args)))
  else:
    return OK(None)

def addDHCP(hoif_name, gateway, netmask, lowerIP, upperIP):
  arg = "--ifname \"%s\" --ip \"%s\" --netmask \"%s\" --lowerip \"%s\" --upperip \"%s\" --enable" % (hoif_name, gateway, netmask, lowerIP, upperIP)
  return vboxManager("dhcpserver", "add %s" % arg) \
    .then(defer(enableDHCP, hoif_name=hoif_name))

def enableDHCP(hoif_name):
  arg = "--ifname \"%s\" --enable" % hoif_name
  return vboxManager("dhcpserver", "modify %s" % arg)
 
def disableDHCP(hoif_name):
  arg = "--ifname \"%s\" --disable" % hoif_name
  return vboxManager("dhcpserver", "modify %s" % arg)
  
def removeDHCP(hoif_name):
  return vboxManager("dhcpserver", "remove --ifname \"%s\"" % hoif_name)

def addHostOnlyInterface():
  def parseResult(r):
    match = re.match("^Interface '(.+?)' was successfully created", r)
    if match:
      return OK(match.group(1))
    else:
      return Fail(VirtualBoxError("Failed to create a new Host Only Interface"))
  return vboxManager("hostonlyif", "create").bind(parseResult) 

def configureHostOnlyInterface(name, ip, netmask):
  net = _netFrom(ip+"/"+netmask)
  if net.isFail():
    return net

  net = net.getOK()
  #if net.version == 6: 
  #  return vboxManager("hostonlyif", "ipconfig \"%s\" --ipv6 \"%s\" --netmasklengthv6 \"%s\"" % (name, net.ip, net.prefixlen))

  return vboxManager("hostonlyif", "ipconfig \"%s\" --ip \"%s\" --netmask \"%s\"" % (name, net.ip, net.netmask)) 

def removeHostOnlyInterface(hoif):
  return removeDHCP(hoif.name) \
    .catch(lambda x: OK(hoif)) \
    .then(defer(vboxManager, "hostonlyif", "remove \"%s\"" % hoif.name))

# -- Private helpers

def _ipFrom(ip):
  try:
    return OK(IPAddress(ip))
  except Exception as err:
    return Fail(err)

def _netFrom(net):
  try:
    return OK(IPNetwork(net))
  except Exception as err:
    return Fail(err)

def _mapAsBlocks(data, func):
  sep = _vboxLineEnding()
  sep = "%s%s" % (sep, sep)
  blocks = [ x for x in data.strip().split(sep) if x ]
  return OK(blocks).mapM(func)

def _extractClassFromBlock(block, actions, cls):
  lines = block.split(_vboxLineEnding())

  info = OrderedDict()
  for expr, field in actions:
    info[field] = None
 
  for line in lines:
    line = line.strip()
    for expr, field in actions:
      match = re.match(expr, line)
      if match:
        info[field] = match.group(1)
        break

  if info:
    return OK(cls(**info))
  else:
    return OK(None)
