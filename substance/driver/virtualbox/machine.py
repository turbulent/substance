import re
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.exceptions import (MachineDoesNotExist, SubstanceDriverError)
from vbox import vboxManager
from exceptions import *

def inspectOVF(ovfFile):
  '''
  Inspect an OVF file to extract it's examined output
  '''
  return vboxManager("import", "-n %s" % ovfFile)

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
  importParams.insert(0, ovfFile)
  return vboxManager("import", " ".join(importParams)) \
    .then(defer(readMachineID, name))

# -- Read functions

def readMachines():
  vboxManager("list", "vms").bind(parseMachinesList)
 
def readMachineID(name):
  '''
  Retrieve the driver specific machine ID for a machine name.
  '''
  return vboxManager("list", "vms") \
    .bind(parseMachinesList) \
    .bind(lambda x: OK(x[name]) if name in x else Fail(MachineDoesNotExist("No Machine ID found for \"%s\"" %name)))

def readMachineInfo(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .bind(parseMachineInfo)

def readMachineExists(uuid):
  return vboxManager("list", "vms").bind(defer(parseMachinesForID, uuid=uuid))
  
def readMachineState(uuid):
  return vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
    .catch(lambda err: OK("inexistent") if err.code is "VBOX_E_OBJECT_NOT_FOUND" else None) \
    .bind(parseMachineState)

def readGuestProperty(uuid, prop):
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
  for line in vms.split("\n"):
    parts = matcher.match(line)
    if parts:
      machines[parts.group(1)] = parts.group(2)
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
  lines = machInfo.split("\n")
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
  Parse the output of showvminfo to extrcat the VM state
  '''
  if re.search(r'^name="<inaccessible>"$', vminfo, re.M):
    return OK('inaccessible')

  stateMatch = re.search(r'^VMState="(.+?)"$', vminfo, re.M)
  if stateMatch:
    return OK(stateMatch.group(1))
  else:
    return OK('inexistent')

def parseGuestProperty(prop): 
  prop = prop.strip()

  if prop == 'No value set!' or not prop:
    return OK(None)

  match = re.match(r'^Value: (.+?)$', prop)
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

# -- Control

def start(uuid):
  return vboxManager("startvm", "--type headless \"%s\"" % (uuid)) \
    .bind(lambda x: OK(uuid))

def halt(uuid):
  return vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid) \
    .bind(lambda x: OK(uuid))

def suspend(uuid):
  return vboxManager("controlvm", "\"%s\" savestate" % uuid) \
    .bind(lambda x: OK(uuid))

def terminate(uuid):
  return vboxManager("controlvm", "\"%s\" poweroff" % uuid) \
    .bind(lambda x: OK(uuid))

def delete(uuid):
  return vboxManager("unregistervm", "--delete \"%s\"" % (uuid)) \
    .bind(lambda x: OK(uuid))

