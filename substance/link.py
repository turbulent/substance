import sys
import os
import logging
import paramiko
from paramiko.py3compat import u
import socket
from time import time
from collections import namedtuple
from substance.monads import *
from substance.exceptions import *
from subprocess import check_output
from substance.termutils import getTerminalSize

logger = logging.getLogger(__name__)

LinkResponse = namedtuple('LinkResponse', ['link','stdin','stdout','stderr', 'code', 'cmd'])

try:
  import termios
  import tty
  hasTermios = True
except ImportError:
  hasTermios = False



class Link(object):
  
  def __init__(self, keyFile, keyFormat="RSA", useAgent=False):
    self.keyFile = keyFile
    self.keyFormat = keyFormat
    self.useAgent = useAgent
    self.key = None
    self.username = "substance"
    self.port = 22
    self.connected = False
    self.client = None
    self.sftp = None

  def waitForConnect(self, maxtries=200, timeout=60):

    start = time()   
    tries = 0

    while not self.connected:
      logger.debug("Connect attempt %s..." % tries)
      state = self.connect()  \
        .catchError(paramiko.ssh_exception.SSHException, lambda err: OK(None)) \
        .catchError(socket.error, lambda err: OK(None)) 
      if state.isFail():
        return state
      if time() - start > timeout:
        return Fail(LinkConnectTimeoutExceeded("Timeout exceeded"))
      if tries >= maxtries:
        return Fail(LinkRetriesExceeded("Max retries exceeded"))
      tries += 1

    end = time()
    logger.debug("Connect time: %ss" % (end-start)) 
    self.connected = True 
    return OK(self)
 
  def connectEngine(self, engine):
    connectDetails = engine.getConnectInfo()
    self.hostname = connectDetails.get('hostname')
    self.port = connectDetails.get('port')
    logger.debug("Connecting to engine %s via %s:%s" % (engine.name, self.hostname, self.port))
    return self.loadKey().then(self.waitForConnect)

  def connectHost(self, host, port):
    self.hostname = host
    self.port = port
    return self.loadKey().then(self.waitForConnect)

  def loadKey(self):
    try:
      if not self.key:
        if self.useAgent:
          keys = paramiko.agent.Agent().get_keys()
          if keys:
            logger.debug("Connecting using key #0 from SSH Agent")
            self.key = keys[0]

      if not self.key:
        logger.debug("Connecting using %s key: %s" % (self.keyFormat, self.keyFile))
        if self.keyFormat == 'DSA':
          self.key = paramiko.dsskey.DSSKey.from_private_key_file(self.keyFile, password=None)
        elif self.keyFormat == 'ECSDA':
          self.key = paramiko.ecdsakey.ECDSAKey.from_private_key_file(self.keyFile, password=None)
        else:
          self.key = paramiko.rsakey.RSAKey.from_private_key_file(self.keyFile, password=None)

    except Exception as err:
      return Fail(err)
    return OK(self.key) 

  def connect(self):
    try:
      self.client = paramiko.SSHClient()
      self.client.load_system_host_keys()
      self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      options = self.getConnectOptions()
      self.client.connect(**options)
      self.connected = True
      return OK(self)
    except Exception as err:
      return Fail(err)

  def getConnectOptions(self):
    return {
      'hostname': self.hostname,
      'port': self.port,
      'username': self.username, 
      'pkey': self.key,
      'allow_agent': True,
      'look_for_keys': True,
      'timeout': 1,
      'banner_timeout': 1
    }

  def command(self, cmd, *args, **kwargs):
    return self.runCommand(cmd, *args, **kwargs) 

  def streamCommand(self, cmd, *args, **kwargs):
     self.runCommand(cmd, stream=True) 

  def runCommand(self, cmd, sudo=False, stream=False, capture=False, interactive=False, shell=False, *args, **kwargs):

    import select
  
    cmd = "sudo %s" % cmd if sudo is True else "%s" % cmd

    logger.debug("LINKCOMMAND: %s" % cmd)

    try:
      oldtty = termios.tcgetattr(sys.stdin)

      # Setup our connection channel with forwarding
      channel = None
      if shell:
        # Set terminal options
        channel = self.client.invoke_shell()
      else:
        channel = self.client.get_transport().open_session()
        channel.get_pty()

      if interactive:
        channel.settimeout(0.0)
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

      forward = paramiko.agent.AgentRequestHandler(channel)

      # Setup our buffers
      bufsize = 1024
      stdin = ''
      stdout = ''
      stderr = ''

      # Star the command stream 
      if shell:
        channel.send(cmd + "\n", *args, **kwargs)
      else:
        channel.exec_command(cmd, *args, **kwargs)


      isAlive = True
      watchHandles = [channel]
      if interactive:
        watchHandles.append(sys.stdin)

      while isAlive:
        self.resizePTY(channel)
        r, w, e = select.select(watchHandles, [], [])

        if channel.exit_status_ready():
          isAlive = False
          break

        if channel in r:
          if channel.recv_ready():
            d = channel.recv(bufsize)
            if len(d) == 0:
              isAlive = False
            else:
              if stream:
                sys.stdout.write(d)
                sys.stdout.flush()
              if capture:
                stdout += d

          if channel.recv_stderr_ready():
            d = channel.recv_stderr(bufsize)
            if stream:
              sys.stderr.write(d)
              sys.stderr.flush()
            if capture:
              stderr += d

        if sys.stdin in r and isAlive and interactive:
          x = os.read(sys.stdin.fileno(), bufsize)
          if len(x) == 0:
            isAlive = False
          else:
            channel.send(x)

      code = channel.recv_exit_status()

      if code != 0:
        return Fail(LinkCommandError(cmd=cmd, message="An error occured when running command." , stdout=stdout, stderr=stderr, code=code, link=self))

      return OK(LinkResponse(link=self, cmd=cmd, stdin=stdin, stdout=stdout, stderr=stderr, code=code))
    except Exception as err:
      logger.debug("%s" % err)
      return Fail(err)
    except KeyboardInterrupt as err:
      return Fail(LinkCommandError(cmd=cmd, message="User Interrupted." , stdout=stdout, stderr=stderr, code=1, link=self))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

  def resizePTY(self, channel):
    tty_width, tty_height = getTerminalSize() 
    try:
      channel.resize_pty(width=int(tty_width), height=int(tty_height))
    except paramiko.ssh_exception.SSHException:
      pass
 
  def getClient(self):
    return self.client

  def getSFTP(self):
    if not self.sftp:
      self.sftp = self.client.open_sftp()
    return self.sftp

  def closeSFTP(self):
    return self.sftp.close()

  def upload(self, localPath, remotePath):
    return Try.attempt(self._put, localPath, remotePath)
    
  def download(self, remotePath, localPath):
    return Try.attempt(self._get, remotePath, localPath)

  def runScript(self, scriptPath, sudo=False):
    scriptName = "/tmp/%s.sh" % time()

    return self.upload(scriptPath, scriptName) \
      .then(defer(self.runCommand, "chmod +x %s" % scriptName, sudo=True)) \
      .then(defer(self.runCommand, cmd=scriptName, sudo=sudo, stream=True))

  def interactive(self, cmd=None):
    if hasTermios:
      return Try.attempt(self._posixShell, cmd)
    else:
      return Try.attempt(self._windowsShell, cmd)

  def _posixShell(self, cmd=None):

    import select

    logger.debug("Opening interactive POSIX shell")
    sys.stdout.write('\r\n*** Begin interactive session.\r\n')
    oldtty = termios.tcgetattr(sys.stdin)

    channel = self.client.get_transport().open_session()
    forward = paramiko.agent.AgentRequestHandler(channel)

    channel.get_pty()
    channel.invoke_shell()

    if cmd:
      channel.send(cmd)
      channel.send("\n")
 
    try:
      tty.setraw(sys.stdin.fileno())
      tty.setcbreak(sys.stdin.fileno())
      channel.settimeout(0.0)

      isAlive = True

      while isAlive:
        self.resizePTY(channel)
        r, w, e = select.select([channel, sys.stdin], [], [])
        if channel in r:
          try:
            x = channel.recv(1024)
            if len(x) == 0:
              isAlive = False
            else:
              sys.stdout.write(x)
              sys.stdout.flush()
          except socket.timeout:
            pass
        if sys.stdin in r and isAlive:
          x = os.read(sys.stdin.fileno(), 1)
          if len(x) == 0:
            isAlive = False
          else:
            channel.send(x)
      channel.shutdown(2)

    finally:
      termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
      sys.stdout.write('\r\n*** End of interactive session.\r\n')

  def _windowsShell(self, cmd=None):
    import threading
  
    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")
        
    def writeall(sock):
      while True:
        data = sock.recv(256)
        if not data:
          sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
          sys.stdout.flush()
          break
        sys.stdout.write(data)
        sys.stdout.flush()
        
    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()
    try:
      while True:
        d = sys.stdin.read(1)
        if not d:
          break
        chan.send(d)
    except EOFError:
      # user hit ^Z or F6
      pass

  def _put(self, localPath, remotePath):
    client = self.getSFTP()
    logger.debug("PUT %s %s" % (localPath, remotePath))
    return client.put(localPath, remotePath) 
       
  def _get(self, remotePath, localPath):
    client = self.getSFTP()
    logger.debug("GET %s %s" % (remotePath, localPath))
    return client.get(remotePath, localPath) 
