
class SubstanceError(Exception):
  '''
  Base class to all substance exceptions
  '''
  errorLabel = ""
  def __init(self, message=''):
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

class SubstanceDriverError(SubstanceError):
  '''
  Driver-specific raised error
  '''

class VmNotFound(SubstanceDriverError):
  '''
  Virtual machine was not found.
  '''

class VirtualBoxError(SubstanceDriverError):
  '''
  Virtual box driver raised error
  ''' 
