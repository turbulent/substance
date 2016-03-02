import os
import logging
import shutil
import shlex
import subprocess
from subprocess import call, Popen, check_output, CalledProcessError
from substance.exceptions import FileSystemError

# pylint: disable=W0232

class Shell(object):

  @staticmethod
  def printConfirm(msg, assumeYes=False):
    logging.info(msg)
    res = raw_input('Proceed? [N/y] ')
    if not res.lower().startswith('y'):
      return False
    logging.info('... proceeding')
    return True

  @staticmethod
  def call(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      returncode = call(cmd, shell=True)
      return (returncode, None)
    except CalledProcessError as err:
      return (err.returncode, err.output)

  @staticmethod
  def command(cmd):
    logging.debug("COMMAND: %s", cmd)
    try:
      out = check_output(cmd, shell=True)
      return (0, out.strip())
    except CalledProcessError as err:
      return (err.returncode, err.output)

  @staticmethod
  def procCommand(cmd):
    try:
      logging.debug("COMMAND: %s", cmd)
      proc = Popen(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      pout, perr = proc.communicate()
      return {"returnCode": proc.returncode, "stdout":pout, "stderr":perr}
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      return {"returnCode":1, "stdout": None, "stderr": None}

  @staticmethod
  def makeDirectory(path, mode=0750):
    if not os.path.exists(path):
      try:
        os.makedirs(path, mode)
      except Exception as err:
        raise FileSystemError("Failed to create %s: %s" % (path, err))

  @staticmethod
  def nukeDirectory(path):
    if path and path is not '/' and path is not 'C:\\':
      shutil.rmtree(path)
