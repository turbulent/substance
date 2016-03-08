
class Monad(object):

  def bind(self, mf):
    raise NotImplementedError

  def map(self, mf):
    raise NotImplementedError

#----------- EITHER

class Maybe(Monad):
  def get(self):
    raise NotImplementedError

  def isNothing(self):
    if isinstance(self, Nothing):
      return True 

  def bind(self, mf):
    if self.isNothing():
      return self
    return mf(self.get())

  def map(self, f):
    if self.isNothing(): 
      return self
    return Just(f(self.get()))

  def getOrElse(self, default):
    return default if self.isNothing() else self.get()
    
class Just(Maybe):
  value = None

  def __init__(self, value):
    self.value = value

  def get(self):
    return self.value

  def __repr__(self):
        return "Just(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, Just):
      return self.value == other.value
    return False

class Nothing(Maybe):
  def get(self):
    raise NoValue

  def __repr__(self):
        return "Nothing"

  def __eq__(self, other):
    return isinstance(other, Nothing)

#----------- EITHER

class Either(Monad):

  def isLeft(self):
    return isinstance(self, Left)
       
  def isRight(self):
    return isinstance(self, Right)

  def getLeft(self):
    raise NotImplementedError

  def getRight(self):
    raise NotImplementedError

  def bind(self, mf):
    if self.isLeft():
      return self
    return mf(self.getRight())
  
  def map(self, mf):
    if self.isLeft():
      return self
    return Right(mf(self.getRight())) 

class Left(Either):
  value = None
  def __init__(self, value):
    self.value = value

  def getLeft(self):
    return self.value

  def __repr__(self):
        return "Left(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.value == other.value
    return False
  
class Right(Either):
  value = None
  def __init__(self, value):
    self.value = value

  def getRight(self):
    return self.value

  def __repr__(self):
        return "Right(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.value == other.value
    return False

#----------- TRY

class Try(Monad):

  def isFail(self):
    return isinstance(self, Fail)
    
  def isOK(self):
    return isinstance(self, OK)

  def getError(self):
    raise NotImplementedError

  def getOK(self):
    raise NotImplementedError

  def bind(self, mf):
    if self.isFail():
      return self
    return mf(self.getOK())

  def map(self, f):
    if self.isFail():
      return self
    return OK(f(self.getOK()))

  def mapError(self, f):
    if self.isOK():
      return self
    return Fail(f(self.getError()))
    
  def catch(self, f):
    return self.then(None, f)  

  def then(self, okF, failF=None):

    if self.isFail(): 
      if failF:
        r = failF(self.getError())
        if isinstance(r, Try):
          return r
        return self
      else:
        return self
    else:
      r = okF()
      if isinstance(r, Try):
        return r
      return OK(r)
      
 
class OK(Try):
  value = None
  def __init__(self, value):
    self.value = value

  def getOK(self):
    return self.value

  def __repr__(self):
        return "OK(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.value == other.value
    return False

class Fail(Try):
  value = None
  def __init__(self, value):
    self.value = value

  def getError(self):
    return self.value

  def __repr__(self):
        return "Fail(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.value == other.value
    return False
