import logging
import functools
from functools import (wraps)
from functools import partial

class Monad(object):

  def bind(self, mf):
    raise NotImplementedError

  def map(self, mf):
    raise NotImplementedError

  def __rshift__(self, f):
    return self.bind(f)

  def __ilshift__(self, f):
    return self.bind(f)

#----------- EITHER

class Maybe(Monad):

  @staticmethod
  def of(value=None):
    if(value is None):
      return Nothing()
    else:
      return Just(value)

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

  @staticmethod
  def of(value):
    return OK(value)

  def isFail(self):
    return isinstance(self, Fail)
    
  def isOK(self):
    return isinstance(self, OK)

  def getError(self):
    raise NotImplementedError

  def getOK(self):
    raise NotImplementedError

  def getOrElse(self, default):
    return default if self.isFail() else self.getOK()

  def bind(self, mf, *args, **kwargs):
    if self.isFail():
      return self
    return mf(self.getOK(), *args, **kwargs)

  def map(self, f):
    if self.isFail():
      return self
    return OK(f(self.getOK()))

  def thenIfTrue(self, f):
    return self.thenIfBool(f, lambda: OK(False))

  def thenIfFalse(self, f):
    return self.thenIfBool(lambda: OK(True), f)

  def thenIfNone(self, f):
    if self.isFail():
      return self
    if self.getOK() is None:
      return self.then(f)
    else:
      return self
        
  def thenIfBool(self, fTrue, fFalse):
    if self.isFail():
      return self
    if self.getOK() is True:
      return self.then(fTrue)
    else:
      return self.then(fFalse)

  def then(self, okF=None, failF=None):
    if self.isFail(): 
      if failF:
        r = failF(self.getError())
        if isinstance(r, Try):
          return r
        return self
      else:
        return self
    else:
      if okF:
        r = okF()
        if isinstance(r, Try):
          return r
        return OK(r)
      else:
        return self

  def catch(self, f):
    return self.then(None, f)  

  def catchError(self, err, f):
    def catcher(x):
      if isinstance(x, err):
        return f(self.getError())
    return self.then(None, catcher)
      
  def bindIfTrue(self, f):
    return self.bindIf(f, lambda x: OK(False))

  def bindIfFalse(self, f):
    return self.bindIf(lambda x: OK(True), f)

  def bindIf(self, fTrue, fFalse):
    if self.isFail():
      return self
    if self.getOK() is True:
      return self.bind(fTrue)
    else:
      return self.bind(fFalse)

  def mapM(self, mf):
    def mapper(xs):
      return mapM(self, mf, xs)
    return self.bind(mapper)

  def mapM_(self, mf):
    def mapper(xs):
      return mapM_(self, mf, xs)
    return self.bind(mapper)

  @staticmethod
  def compose(*funcs):
    def func(x):
      return fold(lambda acc, f: acc.bind(f), funcs, Try.of(x))
    return func

  @staticmethod
  def sequence(monads):
    ''' Fold a list of monads into a monad containing the list of values '''
    return reduce(lambda acc, mv: unshiftM(Try, acc, mv), reversed(monads), Try.of([]))

  @staticmethod
  def attemptDeferred(f, expect=Exception):
    def tryer(*args, **kwargs):
      try:
        return OK(f(*args, **kwargs))
      except expect as e:
        return Fail(e)
    return tryer

  @staticmethod 
  def attempt(f, *args, **kwargs):
    return Try.attemptDeferred(f)(*args, **kwargs)

  @staticmethod 
  def raiseError(self, err=Exception):
    raise(err)

  def join(self):
    return self if self.isFail() else self.getOK()

class OK(Try):
  value = None
  def __init__(self, value):
    self.value = value

  def getOK(self):
    return self.value

  def __repr__(self):
        return "OK(%r)" % self.value

  def __bool__(self):
    return True
 
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

  def __bool__(self):
    return False

  def __repr__(self):
        return "Fail(%r)" % self.value

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.value == other.value
    return False

def fold(f, xs, init=None):
  return functools.reduce(f, xs, init)

def compose(*funcs): 
  def func(x):
    return fold(lambda acc, f: f(acc), reversed(funcs), x)
  return func

def unshiftM(monad, monads, mv): 
  ''' Prepend a monadic value to the list value of a monad '''
  return monads.bind(lambda xs: mv.bind(lambda x: monad.of( [x] + xs)))

def sequence(monad, monads):
  ''' Fold a list of monads into a monad containing the list of values '''
  return reduce(lambda acc, mv: unshiftM(monad, acc, mv), reversed(monads), monad.of([]))

def mapM(monad, mf, xs):
  ''' Map a monadic function over a list of values, lifting them into monadic context and convert the results to a monad containing a list of the values. '''
  mapped = map(mf, xs)
  sequenced = sequence(monad, mapped)
  return sequenced

def mapM_(monad, mf, xs):
  ''' Map a monadic  action to a structure, evaluate from left to right and ignore results. '''
  map(mf, xs)
  return monad.of(xs)

def defer(f, *args, **kwargs):
  fargs = args
  fkwargs = kwargs
  return partial(f, *fargs, **fkwargs)

def failWith(exception):
  return (lambda *x: Fail(exception))

def chainSelf(self, *_, **__):
  return self

def flatten(xs):
  return [ x for sl in xs for x in sl]

#class Retry(Monad):
#
#  @staticmethod
#  def of(func):
#    return RetryContinue(func)
#
#  def isContinue(self):
#    return isinstance(self, Continue)
#
#  def isBreak(self):
#    return isinstance(self, Break)
#
#  def isDone(self):
#    return isinstance(self, Done)
#
#  def call(self):
#    return self.value()
#
#  def bind(self, mf):
#    value = self.call()
#
#    if value.isContinue():
#    elif value.isBreak():
#    elif value.isDone():
#    
#class Continue(Retry):
#  pass
#class Break(Retry):
#  pass
#class Done(Done):
#  pass
#
#Retry(connect, timeout=60, retries=100).bind()
