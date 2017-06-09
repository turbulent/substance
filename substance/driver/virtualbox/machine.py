from __future__ import absolute_import
from builtins import map
from builtins import zip
from builtins import object
import re
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.constants import Constants
from substance.exceptions import (MachineDoesNotExist, SubstanceDriverError)
from .vbox import (vboxManager,_vboxLineEnding)
from .exceptions import *
from substance.shell import Shell
from functools import reduce

logger = logging.getLogger(__name__)

MachineStates = Constants(
  POWEROFF="poweroff",
  SAVED="saved",
  ABORTED="aborted",
  PAUSED="paused",
  STUCK="stuck",
  RESTORING="restoring",
  SNAPSHOTTING="snapshotting",
  SETTING_UP="setting up",
  ONLINE_SNAPSHOTTING="online snapshotting",
  RESTORING_SNAPSHOT="restoring snapshot",
  DELETING_SNAPSHOT="deleting snapshot",
  LIVE_SNAPSHOTTING="live snapshotting",
  RUNNING="running",
  STARTING="starting",
  STOPPING="stopping",
  SAVING="saving",
  UNKNOWN="unknown",
  INACCESSIBLE="inaccessible",
  INEXISTENT="inexistent"
)

AdapterTypes = Constants(
  NONE="none",
  NULL="null",
  NAT="nat",
  HOSTONLY="hostonly",
  NATNET="natnet",
  INTNET="intnet",
  BRIDGED="bridged"
)

class AdapterSettings(object):
  def __init__(self, type, attachedTo, mac=None, promiscuous=False):
    self.type = type
    self.attachedTo = attachedTo
    self.mac = mac
    self.promiscuous = promiscuous

  def getTypeArg(self):
    return {
      AdapterTypes.NAT: 'natnet',
      AdapterTypes.HOSTONLY: 'hostonlyadapter',
      AdapterTypes.NATNET: 'nat-network',
      AdapterTypes.BRIDGED: 'bridgeadapter',
      AdapterTypes.INTNET: 'intnet'
    }.get(self.type, 'natnet')

  def getAsArg(self, nicId=0):
    vals = self.__dict__.copy()
    vals['nicId'] = nicId
    vals['typeArg'] = self.getTypeArg()
    return "--nic%(nicId)d %(type)s --%(typeArg)s%(nicId)d \"%(attachedTo)s\"" % vals

  def __repr__(self):
    return "Adapter(nic=%(nic)s,nictype=%(nictype)s,mac=%(mac)s,promiscuous=%(promiscuous)s" % self.__dict__

class SharedFolder(object):
  def __init__(self, name, hostPath, vboxName=None):
    self.name = name
    self.hostPath = hostPath
    self.vboxName = vboxName

  def __repr__(self):
    return "SharedFolder(%(name)s -> %(hostPath)s, %(vboxName)s)" % self.__dict__

# -- Import API

def inspectOVF(ovfFile):
  '''
  Inspect an OVF file to extract it's examined output
  '''
  return vboxManager("import", '-n "%s"' % Shell.normalizePath(ovfFile))

def makeImportParams(inspection, name, engineProfile=None):
  '''
  Make the import parameter commands based on name, engine profile and inspection
  '''
  suggestedName = re.search(r'Suggested VM name "(.+?)"', inspection)
  if not suggestedName:
    return Fail(SubstanceDriverError("Invalid OVF: File contains no VM Name"))
  else:
    suggestedName = suggestedName.group(1)

  ddebug("OVF Suggested VM Name \"%s\"", name)

  importParams = ["--vsys 0 --vmname \"%s\"" % name]
  if engineProfile:
    importParams.append("--cpus %d" % engineProfile.cpus)
    importParams.append("--memory %d" % engineProfile.memory)

  diskScan = re.compile(r'(\d+): Hard disk image: source image=.+, target path=(.+),')
  for disk in diskScan.findall(inspection):
    diskPath = disk[1]
    diskPath = diskPath.rsplit(suggestedName, 1)
    diskPath = name.join(diskPath)
    importParams.append("--unit %s --disk \"%s\"" % (disk[0], diskPath))

  return OK(importParams)

def importOVF(importParams, name, ovfFile):
  '''
  Import the OVF file as a virtual box vm.
  '''
  ovfFile = Shell.normalizePath(ovfFile)
  importParams.insert(0, '"'+ovfFile+'"')
  return vboxManager("import", " ".join(importParams)) \
    .then(defer(readMachineID, name))

# -- Read functions

def readMachines():
  return vboxManager("list", "vms").bind(parseMachinesList)
 
def readMachineID(name):
  '''
  Retrieve the driver specific machine ID for a machine name.
  '''
  def findMachineID(machs):
    revmach = dict(list(zip(list(machs.values()), list(machs.keys()))))
    return OK(revmach[name]) if name in revmach else Fail(MachineDoesNotExist("No Machine ID found for \"%s\"" %name))

  return vboxManager("list", "vms") \
    .bind(parseMachinesList) \
    >> findMachineID

def readMachineInfo(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .bind(parseMachineInfo)

def readMachineExists(uuid):
  return vboxManager("list", "vms").bind(defer(parseMachinesForID, uuid=uuid))
  
def readMachineState(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .catch(lambda err: OK("inexistent") if err.code == "VBOX_E_OBJECT_NOT_FOUND" else Fail(err)) \
    .bind(parseMachineState)

def readWaitGuestProperty(uuid, pattern, timeout=1000):
  logger.debug("Read wait(%ss) on pattern %s on %s" % (timeout, pattern, uuid))
  return vboxManager("guestproperty", "wait %s %s --timeout %s" % (uuid, pattern, timeout)) 
  
def readGuestProperty(uuid, prop):
  logger.debug("Read guest property %s on %s" % (prop, uuid))
  return vboxManager("guestproperty", "get %s %s" % (uuid, prop)) \
    .bind(parseGuestProperty)

def readGuestAddVersion(uuid):
  return readGuestProperty(uuid, "/VirtualBox/GuestAdd/Version") \
    .bind(parseGuestAddVersion)

#-- Parsing functions

def parseMachinesList(vms):
  '''
  Parse the output of "list vms" and return a dict of machine name to machine id.
  '''
  matcher = re.compile(r'"([^"]+)" {([^}]+)}')
  machines = {}
  for line in vms.split(_vboxLineEnding()):
    parts = matcher.match(line)
    if parts:
      machines[parts.group(2)] = parts.group(1)
  return OK(machines)
  
def parseMachinesForID(vms, uuid):
  '''
  Parse the output of list vms to find if uuid exists.
  '''
  if re.search(r'"([^"]+)" {'+re.escape(uuid)+'}', vms, re.M):
    return OK(True)
  else:
    return OK(False)

def parseMachineInfo(machInfo):
  '''
  Parse Virtual Box machine info into a dict.
  '''
  lines = machInfo.split(_vboxLineEnding())
  machDict = OrderedDict()
  #rotKey = OrderedDict()
  for line in lines:
    try:
      var, value = line.split("=", 1)
      value = value.strip('"')
      #if not var in rotKey:
      #  rotKey[var] = 0
      #if var in machDict:
      #  rotKey[var] += 1
      #vark = var+"_%s" % rotKey[var]
      machDict[var] = value
    except ValueError:
      pass
  return OK(machDict)

def parseMachineState(vminfo):
  '''
  Parse the output of showvminfo to extract the VM state
  '''
  if re.search(r'^name="<inaccessible>"\r?\n', vminfo, re.MULTILINE):
    return OK('inaccessible')

  stateMatch = re.search(r'^VMState="(.+?)"\r?\n', vminfo, re.MULTILINE)
  if stateMatch:
    return OK(stateMatch.group(1))
  else:
    return OK('inexistent')

def parseGuestProperty(prop): 
  prop = prop.strip()

  if prop == 'No value set!' or not prop:
    return OK(None)

  match = re.match(r'^Value: (.+?)$', prop)
  logger.debug("Guest Property: %s" % prop)
  if match:
    return OK(match.group(1))
  else:
    return Fail(VirtualBoxError(None, "Failed to to parse guest property output : %s" % prop))

def parseGuestAddVersion(guestAdd):
  if guestAdd is None:
    return Fail(VirtualBoxMissingAdditions("VirtualBox guest additions are not installed."))

  parts = guestAdd.split("_", 1)
  if len(parts) >= 1:
    return OK(parts[0])
  else:
    return Fail(VirtualBoxMissingAdditions("VirtualBox guest additions are not installed."))

def parseSharedFolders(machInfo):
  def extractFolders(acc, k):
    match = re.match(r'^SharedFolderNameMachineMapping(\d+)', k)
    if match:
      idx = match.group(1)
      acc.append(SharedFolder(name=machInfo[k], hostPath=machInfo["SharedFolderPathMachineMapping%s"%idx], vboxName=k))
    return acc

  return OK(reduce(extractFolders, list(machInfo.keys()), []))
 
# -- Modify

def configureAdapter(uuid, adapterId, adapterSettings):
  return vboxManager("modifyvm", "\"%s\" %s" % (uuid, adapterSettings.getAsArg(adapterId)))

def configureProfile(uuid, cpus, memory):
  return vboxManager("modifyvm", "\"%s\" --cpus %s --memory %s" % (uuid, cpus, memory))
  
# -- Control

def start(uuid):
  return vboxManager("startvm", "--type headless \"%s\"" % (uuid)) \
    .bind(lambda x: OK(uuid))

def halt(uuid):
  return vboxManager("controlvm", "\"%s\" poweroff soft" % uuid) \
    .bind(lambda x: OK(uuid))

def suspend(uuid):
  return vboxManager("controlvm", "\"%s\" savestate" % uuid) \
    .bind(lambda x: OK(uuid))

def pause(uuid):
  return vboxManager("controlvm", "\"%s\" pause" % uuid) \
    .bind(lambda x: OK(uuid))

def resume(uuid):
  return vboxManager("controlvm", "\"%s\" resume" % uuid) \
    .bind(lambda x: OK(uuid))

def terminate(uuid):
  return vboxManager("controlvm", "\"%s\" poweroff" % uuid) \
    .bind(lambda x: OK(uuid))

def delete(uuid):
  return vboxManager("unregistervm", "--delete \"%s\"" % (uuid)) \
    .bind(lambda x: OK(uuid))

# -- Shared Folders

def addSharedFolder(folder, uuid):
  return vboxManager("sharedfolder", "add \"%s\" --name \"%s\" --hostpath \"%s\"" % (uuid, folder.name, folder.hostPath)) \
    .then(defer(enableSharedFolderSymlinks, folder=folder, uuid=uuid))

def enableSharedFolderSymlinks(folder, uuid):
  symlinksKey = "VBoxInternal2/SharedFoldersEnableSymlinksCreate/%s" % folder.name
  return vboxManager("setextradata", "\"%s\" \"%s\" \"%s\"" % (uuid, symlinksKey, 1))

def removeSharedFolder(folder, uuid):
  return vboxManager("sharedfolder", "remove \"%s\" --name \"%s\"" % (uuid, folder.name))

def addSharedFolders(folders, uuid):
  return OK(list(map(defer(addSharedFolder, uuid=uuid), folders)))

def removeSharedFolders(folders, uuid):
  return OK(list(map(defer(removeSharedFolder, uuid=uuid), folders)))

def clearSharedFolders(uuid):
  return readSharedFolders(uuid) \
    .bind(removeSharedFolders, uuid=uuid)

def readSharedFolders(uuid):
  return readMachineInfo(uuid) \
    .bind(parseSharedFolders)
