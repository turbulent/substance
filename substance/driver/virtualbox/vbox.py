import re

from substance.shell import Shell
from substance.monads import *
from substance.logs import *
from exceptions import *
from substance.exceptions import *

def vboxManager(cmd, params=""):
  '''
  Invoke the VirtualBoxManager
  '''
  return Shell.procCommand("%s %s %s" % ("VBoxManage", cmd, params)) \
    .bind(onVboxCommand) \
    .catch(onVboxError)

def onVboxCommand(sh):
  return OK(sh.get('stdout', ''))

def onVboxError(err):
  if isinstance(err, ShellCommandError):
    codeMatch = re.search(r'error: Details: code (VBOX_[A-Z_0-9]*)', err.stderr, re.M)
    code = codeMatch.group(1) if codeMatch else None
    return Fail(VirtualBoxError(message=err.stderr, code=code))


def readVersion():
  return vboxManager("--version").bind(parseVersion)


def parseVersion(vstring):
  fail = Fail(VirtualBoxVersionError("Invalid version of VirtualBox installed."))

  vstring = vstring.strip()
  if vstring is None or vstring == "":
    return fail

  parts = vstring.split("_")
  if len(parts) == 0:
    return fail

  return OK(parts[0].split("r")[0])

