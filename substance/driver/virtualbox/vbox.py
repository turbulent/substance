from __future__ import absolute_import
from builtins import range
import re
import os
import platform
import sys

from substance.shell import Shell
from substance.monads import *
from substance.logs import *
from .exceptions import *
from substance.exceptions import *

VBOX_VERSION_MIN = (5,0,0)
VBOX_VERSION_CHECKED = None

def vboxManager(cmd, params=""):
  '''
  Invoke the VirtualBoxManager
  '''
  return assertVirtualBoxVersion().then(defer(vboxExec, cmd, params))

def vboxExec(cmd, params=""):
  return Shell.procCommand("%s %s %s" % ("VBoxManage", cmd, params)) \
    .bind(onVboxCommand) \
    .catch(onVboxError)

def onVboxCommand(sh):
  return OK(sh.get('stdout', '').decode(sys.stdout.encoding))

def onVboxError(err):
  if isinstance(err, ShellCommandError):
    codeMatch = re.search(r'error: Details: code (VBOX_[A-Z_0-9]*)', err.stderr.decode(sys.stderr.encoding), re.M)
    code = codeMatch.group(1) if codeMatch else None
    return Fail(VirtualBoxError(message=err.stderr, code=code))

def readVersion():
  return vboxExec("--version").bind(parseVersion)

def parseVersion(vstring):
  fail = Fail(VirtualBoxVersionError("Invalid version of VirtualBox installed : %s" % vstring))

  vstring = vstring.strip()
  if vstring is None or vstring == "":
    return fail

  parts = vstring.split("_")
  if len(parts) == 0:
    return fail
 
  return OK(parts[0].split("r")[0])

def assertVirtualBoxVersion():
  global VBOX_VERSION_CHECKED
  if VBOX_VERSION_CHECKED:
    return OK(VBOX_VERSION_CHECKED)
  else:
    return readVersion().bind(checkVersion).bind(saveVersion)

def saveVersion(vstring):
  global VBOX_VERSION_CHECKED
  VBOX_VERSION_CHECKED = vstring
  return OK(vstring)

def checkVersion(vstring):
  semver = vstring.split('.')
  semvercheck = tuple(1 for i in range(0,3) if int(semver[i]) >= VBOX_VERSION_MIN[i])
  if semvercheck == (1,1,1):
    return OK(vstring)
  else:
    msg = "VirtualBox version %s and up is required. %s currently installed." % (VBOX_VERSION_MIN, vstring)
    return Fail(VirtualBoxVersionError(msg))

def _vboxLineEnding():
  if platform.system().startswith("CYGWIN"):
    # Special case: os.linesep reports LF because of Cygwin but VBoxManage will output CRLF because of Windows
    return "\r\n"
  return os.linesep
