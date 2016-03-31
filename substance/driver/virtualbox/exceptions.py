from substance.exceptions import (SubstanceDriverError)

class VirtualBoxError(SubstanceDriverError):
  '''
  Virtual box driver raised error
  '''
  code = None
  def __init__(self, code=None, message=''):
    super(VirtualBoxError, self).__init__(message)
    self.code = code

class VirtualBoxMissingAdditions(SubstanceDriverError):
  '''
  The Virtual Box guest additions are missing.
  '''

class VirtualBoxVersionError(SubstanceDriverError):
  '''
  Wrong version of the Virtual Box system is installed.
  '''

class VirtualBoxObjectNotFound(SubstanceDriverError):
  '''
  Tried to read unknown object
  '''
