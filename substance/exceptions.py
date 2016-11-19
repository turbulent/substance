# -*- coding: utf-8 -*-
# $Id$

class SubstanceError(Exception):
  '''
  Base class to all substance exceptions
  '''
  errorLabel = ""
  def __init__(self, message=''):
    super(SubstanceError, self).__init__(message)
    self.errorLabel = message

class InvalidCommandError(SubstanceError):
  '''
  Raised when an invalid command is passed to CLI
  '''

class InvalidOptionError(SubstanceError):
  '''
  Raised when an invalid option is passed to CLI
  '''

class ShellCommandError(SubstanceError):
  def __init__(self, code=None, message='', stdout='', stderr='', cmd=''):
    super(SubstanceError, self).__init__(message)
    self.code = code
    self.stdout = stdout
    self.stderr = stderr
    self.cmd = cmd

class UserInterruptError(SubstanceError):
  '''
  Raised when a shell command is interrupted by the user.
  '''
 
class FileSystemError(SubstanceError):
  '''
  Raised when substance fails to read or write to the filesystem
  '''
class FileDoesNotExist(SubstanceError):
  '''
  Raised when a file expected to be there does not exist.
  '''

class ConfigSyntaxError(SubstanceError):
  '''
  Raised when invalid syntax was found in a configuration file.
  '''

class ConfigValidationError(SubstanceError):
  '''
  Raised when configuration does not validate.
  '''

class EngineError(SubstanceError):
  '''
  Engine error class
  '''
  engine = None
  def __init__(self, message='', engine=None):
    super(SubstanceError, self).__init__(message)
    self.engine = engine

class EngineExistsError(EngineError):
  '''
  Raised when an engine with the same name exists.
  '''

class EngineNotFoundError(EngineError):
  '''
  Raised when a specified engine was not found
  '''

class EngineNotProvisioned(EngineError):
  '''
  Engine VM is not provided. (ex. does not exist)
  '''

class EngineProvisioned(EngineError):
  '''
  Raised when an engine is provisioned and remove call is initiated.
  '''

class EngineAlreadyProvisioned(EngineError):
  '''
  Engine VM is already provided.
  '''

class EngineAlreadyRunning(EngineError):
  '''
  Engine VM is already running.
  '''
class EngineNotRunning(EngineError):
  '''
  Engine VM is not running.
  '''

class EnvNotDefinedError(EngineError):
  '''
  Raised when an env is not defined on an engine
  '''

class EnvNotFoundError(EngineError):
  '''
  Raised when an env is not found
  '''
  
class SubstanceDriverError(SubstanceError):
  '''
  Driver-specific raised error
  '''

class MachineDoesNotExist(SubstanceDriverError):
  '''
  Machine does not exist
  '''

class LinkConnectTimeoutExceeded(SubstanceError):
  '''
  Link connect timeout exceeded
  '''
 
class LinkTimeoutExceeded(SubstanceError):
  '''
  Link timeout exceeded
  '''

class LinkRetriesExceeded(SubstanceError):
  '''
  Link retries exceeded
  '''
class LinkCommandError(ShellCommandError):
  '''
  Link command error
  '''
  def __init__(self, code=None, message='', stdout='', stderr='', cmd='', link=None):
    super(SubstanceError, self).__init__(message)
    self.code = code
    self.stdout = stdout
    self.stderr = stderr
    self.cmd = cmd
    self.link = link

class BoxError(SubstanceError):
  '''
  Box error category
  '''

class InvalidBoxName(BoxError):
  '''
  Name of box was not formatted correctly
  '''

class BoxArchiveHashMismatch(BoxError):
  '''
  Raised when a box archive hash does not match the registry.
  '''

class SubenvError(SubstanceError):
  '''
  Subenv errors
  '''

class InvalidEnvError(SubenvError):
  '''
  Raised when an invalid env is specified
  '''
