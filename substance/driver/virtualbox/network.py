import re
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from exceptions import *
from vbox import (vboxManager)

class ForwardedPort(object):
  def __init__(self, name, nic, proto, hostIP, hostPort, guestIP, guestPort):
    self.name = name
    self.nic = nic
    self.proto = proto
    self.hostIP = hostIP 
    self.hostPort = hostPort
    self.guestIP = guestIP
    self.guestPort = guestPort

  def __repr__(self):
    return "%(name)s forward %(proto)s host(%(hostIP)s:%(hostPort)s) -> guest(%(guestIP)s:%(guestPort)s)" % self.__dict__

class Network(object):
  def __init__(self, name, networkName, gateway, mask, lowerIP, upperIP, enabled):
    self.name = name
    self.networkName = name
    self.gateway = gateway
    self.mask = mask
    self.lowerIP = lowerIP
    self.upperIP = upperIP
    self.enabled = True if enabled == "Yes" else False

  def __repr__(self):
    rep = "network %(name)s gateway: %(gateway)s netmask %(mask)s (%(lowerIP)s to %(upperIP)s)" % self.__dict__
    rep += " enabled" if self.enabled else ""
    return rep 

# -- Read funcs

def readForwardedPorts(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .bind(parseForwardedPorts)

def readNetworks(self):
  return vboxManager("list", "dhcpservers").bind(parseNetworks)

# -- Parse funcs

def parseNetworks(vmnets):
  '''
  Parse virtual box dhcpservers into Network (s)
  '''
  blocks = vmnets.strip().split("\n\n")
  return OK(blocks).mapM(parseNetworkBlock)

def parseNetworkBlock(block):

  actions = (
    (r'^NetworkName:\s+HostInterfaceNetworking-(.+?)$', 'name'),
    (r'^NetworkName:\s+(HostInterfaceNetworking-(.+?))$', 'networkName'),
    (r'^IP:\s+(.+?)$', 'gateway'),
    (r'^NetworkMask:\s+(.+?)$', 'mask'),
    (r'^lowerIPAddress:\s+(.+?)$', 'lowerIP'),  
    (r'^upperIPAddress:\s+(.+?)$', 'upperIP'),  
    (r'Enabled:\s+(.+?)$', 'enabled')
  )

  lines = block.split("\n")
  netinfo = OrderedDict()
  for line in lines:
    line = line.strip()
    for expr, field in actions:
      match = re.match(expr, line)
      if match:
        netinfo[field] = match.group(1)

  return OK(Network(**netinfo))
      
def parseForwardedPorts(vminfo):
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
      ports.append(ForwardedPort(
        nic=nic,
        name=portmatch.group(1),
        proto=portmatch.group(2),
        hostIP=portmatch.group(3),
        hostPort=portmatch.group(4),
        guestIP=portmatch.group(5),
        guestPort=portmatch.group(6)
      ))

  return OK(ports)

 
