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

class InvalidOptionError(SubstanceError):
  '''
  Raised when an invalid option is passed to CLI
  '''

class ShellCommandError(SubstanceError):
  code = None
  stdout = None
  stderr = None
  def __init__(self, code=None, message='', stdout='', stderr=''):
    super(SubstanceError, self).__init__(message)
    self.code = code
    self.stdout = stdout
    self.stderr = stderr

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

class SubstanceDriverError(SubstanceError):
  '''
  Driver-specific raised error
  '''

class VirtualBoxError(SubstanceDriverError):
  '''
  Virtual box driver raised error
  '''
  code = None
  def __init__(self, code=None, message=''):
    super(VirtualBoxError, self).__init__(message)
    self.code = code
