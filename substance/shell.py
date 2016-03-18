import os
import logging
import shutil
import shlex
import subprocess
from subprocess import call, Popen, check_output, CalledProcessError
from substance.exceptions import FileSystemError
from substance.monads import *

# pylint: disable=W0232

class Shell(object):

  @staticmethod
  def printConfirm(msg, assumeYes=False):
    logging.info(msg)
    res = raw_input('Proceed? [N/y] ')
    if assumeYes or res.lower().startswith('y'):
      logging.info('... proceeding')
      return OK(True)
    return Fail(ShellCommandError(code=0, message="User interrupted."))

  @staticmethod
  def call(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      returncode = call(cmd, shell=True)
      return OK({"code": returncode, "stdout": None})
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))

  @staticmethod
  def command(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      out = check_output(cmd, shell=True)
      return OK({"code":0, "stdout":out.strip()})
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))

  @staticmethod
  def procCommand(cmd):
    try:
      logging.debug("COMMAND: %s", cmd)
      proc = Popen(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      pout, perr = proc.communicate()
      return OK({"code": proc.returncode, "stdout":pout, "stderr":perr})
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      return Fail(ShellCommandError(code=1, message="User Interrupted"))

  @staticmethod
  def makeDirectory(path, mode=0750):
    if not os.path.exists(path):
      try:
        os.makedirs(path, mode)
      except Exception as err:
        return Fail(ShellCommandError(code=1, message="Failed to create %s: %s" % (path,err)))
    return OK(path)

  @staticmethod
  def pathExists(path):
    return OK(path) if os.path.exists(path) else Fail(FileSystemError("Path %s does not exist." % path))

  @staticmethod
  def nukeDirectory(path):
    try:
      if path and path is not '/' and path is not 'C:\\':
        shutil.rmtree(path)
      return OK()
    except Exception as err:
      return Fail(ShellCommandError(code=1, message="Failed to rmtree: %s: %s" % (path,err)))
