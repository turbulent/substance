import re
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from exceptions import *
from vbox import (vboxManager)

# -- Structs

class PortForward(object):
  def __init__(self, name, nic, proto, hostIP, hostPort, guestIP, guestPort):
    self.name = name
    self.nic = nic
    self.proto = proto
    self.hostIP = hostIP 
    self.hostPort = hostPort
    self.guestIP = guestIP
    self.guestPort = guestPort

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
  def __init__(self, interface, serverName, gateway, mask, lowerIP, upperIP, enabled):
    self.interface = interface
    self.serverName = serverName
    self.gateway = gateway
    self.mask = mask
    self.lowerIP = lowerIP
    self.upperIP = upperIP
    self.enabled = True if enabled == True or enabled == "Yes" else False

  def __repr__(self):
    rep = "DHCP(%(interface)s gateway: %(gateway)s netmask %(mask)s (%(lowerIP)s to %(upperIP)s))" % self.__dict__
    rep += " enabled" if self.enabled else ""
    return rep 

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__repr__() == other.__repr__()
    return False

  def getCreateArgs(self):
    return "--ifname %(interface)s --ip %(gateway)s --netmask %(mask)s --lowerip %(lowerIP)s --upperip %(upperIP)s --enable" % self.__dict__

  def getRemoveArgs(self):
    return "--netname %(serverName)s" % self.__dict__

class HostOnlyInterface(object):
  def __init__(self, name, mac, v4ip, v4mask, v6ip, v6prefix, status, dhcpEnabled, dhcpName):
    self.name = name
    self.mac = mac
    self.v4ip = v4ip
    self.v4mask = v4mask
    self.v6ip = v6ip
    self.v6prefix = v6prefix
    self.status = status
    self.dhcpEnabled = True if dhcpEnabled == "Enabled" or dhcpEnabled is True else False
    self.dhcpName = dhcpName
    
  def __repr__(self):
    return "HostOnlyInterface(%(name)s, %(mac)s IP: %(v4ip)s, netmask: %(v4mask)s, IPV6: %(v6ip)s, prefix: %(v6prefix)s status: %(status)s)" % self.__dict__
 
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__repr__() == other.__repr__()
    return False 

# -- Read funcs

def readPortForwards(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .bind(parsePortForwards)

def readDHCPs():
  return vboxManager("list", "dhcpservers") \
    .bind(defer(_mapAsBlocks, func=parseDHCPBlock))

def readDHCP(name):
  return readDHCPs() >> defer(filterDHCP(name=name))

def readHostOnlyInterfaces():
  return vboxManager("list", "hostonlyifs") \
    .bind(defer(_mapAsBlocks, func=parseHostOnlyInterfaceBlock))

def filterDHCP(dhcps, hoif):
  dhcp = next((dhcp for dhcp in dhcps if dhcp.interface == hoif), None)
  return OK(dhcp) if dhcp else Fail(VirtualBoxError("DHCP for interface %s was not found." % name))

# -- Parse funcs

def parseDHCPBlock(block):
  actions = (
    (r'^NetworkName:\s+HostInterfaceNetworking-(.+?)$', 'interface'),
    (r'^NetworkName:\s+(HostInterfaceNetworking-(.+?))$', 'serverName'),
    (r'^IP:\s+(.+?)$', 'gateway'),
    (r'^NetworkMask:\s+(.+?)$', 'mask'),
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
    (r'^DHCP:\s+(.+?)$', 'dhcpEnabled'),
    (r'^VBoxNetworkName:\s+(.+?)$', 'dhcpName'),
    (r'^HardwareAddress:\s+(.+?)$', 'mac'),
  )
  return _extractClassFromBlock(block, actions, HostOnlyInterface)
      
def parsePortForwards(vminfo):
  '''
  Parse Virtual Box machine info for forwarded ports.
  '''
  lines = vminfo.split("\n")
  ports = []
  nic = None
  for line in lines:
    line = line.strip()

    #First match a nic from the info values
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

def clearAllPortForwards(uuid):
  return readPortForwards(uuid).bind(defer(removePortForwards, uuid=uuid))

def removePortForwards(ports, uuid):
  args = []
  for port in ports:
    args.append(port.getDeleteArg())
  
  if len(args) > 0: 
    return vboxManager("modifyvm", "%s %s" % (uuid, " ".join(args)))
  else:
    return OK(None)

def addPortForwards(ports, uuid):
  args = []
  for port in ports:
    args.append(port.getCreateArg())

  if len(args) > 0:
    return vboxManager("modifyvm", "%s %s" % (uuid, " ".join(args)))
  else:
    return OK(None)

def addDHCP(dhcp):
  return vboxManager("dhcpserver", "add %s" % dhcp.getCreateArgs())

def removeDHCP(dhcp):
  return vboxManager("dhcpserver", "remove %s" % dhcp.getDeleteArgs())

#VBoxManage hostonlyif create
#VBoxManage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1
#VBoxManage dhcpserver add --ifname vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0 --lowerip 192.168.56.100 --upperip 192.168.56.200
#VBoxManage dhcpserver modify --ifname vboxnet0 --enable


# -- Private helpers

def _mapAsBlocks(data, func):
  blocks = data.strip().split("\n\n")
  return OK(blocks).mapM(func)

def _extractClassFromBlock(block, actions, cls):
  lines = block.split("\n")

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
  return OK(cls(**info))
