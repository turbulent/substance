import sys
import os
import logging
from subprocess import call, Popen, check_output, CalledProcessError

class Shell:

  @staticmethod
  def printConfirm(msg, assumeYes=False):
    logging.info(msg)
    res = raw_input('Proceed? [N/y] ')
    if not res.lower().startswith('y'):
      return False
    logging.info('... proceeding')
    return True

  @staticmethod
  def shellCommand(self, cmd):
    logging.debug("COMMAND: %s" % cmd)
    try:
      out = check_output(cmd, shell=True)
      return ( 0, out.strip() )
    except CalledProcessError as err:
      return ( err.returncode, err.output )
  
  @staticmethod
  def procCommand(self, cmd):
    try:
      logging.debug("COMMAND: %s" % cmd)
      proc = Popen(cmd, shell=False)
      proc.communicate()
      return proc.returncode
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      return 1 
