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

class FileSystemError(SubstanceError):
  '''
  Raised when substance fails to read or write to the filesystem
  '''

class ConfigSyntaxError(SubstanceError):
  '''
  Raised when invalid syntax was found in a configuration file.
  '''

class EngineExistsError(SubstanceError):
  '''
  Raised when an engine with the same name exists.
  '''

class EngineNotFoundError(SubstanceError):
  '''
  Raised when a specified engine was not found
  '''

class EngineNotProvisioned(SubstanceError):
  '''
  Engine VM is not provided. (ex. does not exist)
  '''

class EngineAlreadyRunning(SubstanceError):
  '''
  Engine VM is already running.
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
