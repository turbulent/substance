import os
import logging
import shutil
import shlex
import subprocess
from subprocess import call, Popen, check_output, CalledProcessError
from substance.exceptions import (FileSystemError, ShellCommandError, UserInterruptError)
from substance.monads import *

# pylint: disable=W0232

class Shell(object):

  @staticmethod
  def printConfirm(msg, assumeYes=False):
    if assumeYes:
      return OK(True)

    logging.info(msg)
    try:
      res = raw_input('Proceed? [N/y] ')
      if res.lower().startswith('y'):
        logging.info('... proceeding')
        return OK(True)
      return Fail(UserInterruptError(message="User interrupted."))
    except KeyboardInterrupt as err:
      return Fail(UserInterruptError(message="User interrupted."))


  @staticmethod
  def call(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      returncode = call(cmd, shell=True)
      if returncode == 0:
        return OK(None)
      else:
        return Fail(ShellCommandError(code=returncode))
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))

  @staticmethod
  def command(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      out = check_output(cmd, shell=True)
      return OK(out.strip())
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))

  @staticmethod
  def procCommand(cmd):
    try:
      logging.debug("COMMAND: %s", cmd)
      proc = Popen(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      pout, perr = proc.communicate()
      if proc.returncode == 0:
        return OK({"stdout": pout, "stderr": perr})
      else:
        return Fail(ShellCommandError(code=proc.returncode, message=pout, stdout=pout, stderr=perr))
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      return Fail(UserInterruptError())

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
      return OK(None)
    except Exception as err:
      return Fail(ShellCommandError(code=1, message="Failed to rmtree: %s: %s" % (path,err)))
