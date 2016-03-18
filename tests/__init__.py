import unittest
from substance.monads import *

class TestMonads(unittest.TestCase):

  def testJust(self):
    self.assertTrue(Just(5) == Just(5))
    self.assertFalse(Just(5) == Just(3))
    self.assertEqual(Just(10), Just(5).map(lambda i: i*2))
    self.assertEqual(Just(10), Just(5).bind(lambda x: Just(x*2)))

  def testOperators(self):
    base = Just(10)

    testRshift = Just(5) >> (lambda x: Just(x*2))
    self.assertEqual(base, testRshift)

    testLshift = Just(5)
    testLshift <<= (lambda x: Just(x*2)) 
    self.assertEqual(base, testLshift)

    self.assertTrue(isinstance(Maybe.of(True), Just))    
    self.assertTrue(isinstance(Maybe.of(None), Nothing))    
    self.assertTrue(isinstance(Maybe.of(), Nothing))    
    self.assertTrue(isinstance(Maybe.of(False), Just))    
    self.assertTrue(isinstance(Maybe.of(""), Just))    
    self.assertTrue(isinstance(Maybe.of(1), Just))    

  def testNothing(self):
    self.assertTrue(Nothing() == Nothing())
    self.assertFalse(Nothing() == Just(5))
    self.assertEqual(Nothing(), Nothing().map(lambda x: x*100))
    self.assertEqual(Nothing(), Nothing().bind(lambda x: Just(x*2)))

  def testMaybe(self):
    maybe = Just(5).map(lambda x: x*2).bind(lambda x: Nothing()).map(lambda x: x*2)
    self.assertEqual(Nothing(), maybe)

    maybe2 = Just(5).map(lambda x: x*2).bind(lambda x: Just(x+10)).map(lambda x: x*2)
    self.assertEqual(Just(40), maybe2)

  def testRight(self):
    self.assertTrue(Right(5) == Right(5))
    self.assertFalse(Right(5) == Right(10))
    self.assertEqual(Right(10), Right(5).map(lambda x: x*2))
    self.assertEqual(Right(10), Right(5).bind(lambda x: Right(x*2)))
    self.assertEqual("%s" % Right(10), "Right(10)")

  def testLeft(self):
    self.assertTrue(Left(5) == Left(5))
    self.assertFalse(Left(5) == Left(10))
    self.assertEqual(Left(5), Left(5).map(lambda x: x*2))
    self.assertEqual(Left(5), Left(5).bind(lambda x: Left(x*2)))
    self.assertEqual("%s" % Left(5), "Left(5)")

  def testEither(self):
    either = Right(5).map(lambda x: x*2).bind(lambda x: Left("Did not work")).map(lambda x: x*2)
    self.assertEqual(Left("Did not work"), either)
    either2 = Right(5).map(lambda x: x*2).bind(lambda x: Right(x+10)).map(lambda x: x*2)
    self.assertEqual(Right(40), either2)

  def testOK(self):
    self.assertTrue(OK(5) == OK(5))
    self.assertFalse(OK(5) == OK(10))
    self.assertEqual(OK(10), OK(5).map(lambda x: x*2))
    self.assertEqual(OK(10), OK(5).bind(lambda x: OK(x*2)))
    self.assertEqual("%s" % OK(5), "OK(5)")

  def testFail(self):
    valError = ValueError()
    synError = SyntaxError()
    self.assertTrue(Fail(valError) == Fail(valError))
    self.assertFalse(Fail(valError) == Fail(synError))
    self.assertEqual(Fail(valError), Fail(valError).map(lambda x: x*2))
    self.assertEqual(Fail(valError), Fail(valError).bind(lambda x: OK(x*2)))
    self.assertEqual("%s" % Fail(valError), "Fail(ValueError())")
    self.assertEqual(Fail(valError), Fail(valError).catch(lambda x: 1337))

  def testTry(self):
    valError = ValueError()
    synError = SyntaxError()

    t3y = OK(10).map(lambda x: x*2).bind(lambda x: Fail(valError)).map(lambda x: x*2)
    self.assertEqual(Fail(valError), t3y)

    t3y2 = OK(10).map(lambda x: x*2).bind(lambda x: OK(50)).map(lambda x: x*2)
    self.assertEqual(OK(100), t3y2)

  def testTryAttempt(self):

    t3r3 = Try.attempt(lambda: "Foo")
    self.assertEqual(OK("Foo"), t3r3)  

    t3r3 = Try.attempt(Try.raiseError)
    self.assertEqual(t3r3.__class__.__name__, "Fail")  
     
  def testTryThen(self):
    valError = ValueError()
    synError = SyntaxError()
    attempt = (OK(10) 
      .then(lambda: OK(20))
      .then(lambda: OK(30)) 
      .then(lambda: OK(40)))

    self.assertEqual(OK(40), attempt)

    attempt2 = (OK(10) 
      .then(lambda: OK(20)) 
      .then(lambda: Fail(synError)) 
      .then(lambda: OK(40)))

    self.assertEqual(Fail(synError), attempt2)

    attemptRecover = (OK(10)
      .then(lambda: OK(20))
      .then(lambda: Fail(valError))
      .then(lambda: OK(40))
      .catch(lambda err: OK("Recovered")))
    self.assertEqual(OK("Recovered"), attemptRecover)

    attemptFail = (OK(10)
      .then(lambda: OK(20))
      .then(lambda: Fail(valError))
      .then(lambda: OK(40))
      .catch(lambda err: "foo"))

    self.assertEqual(Fail(valError), attemptFail)

    attemptReraise = (OK(10)
      .then(lambda: OK(20))
      .then(lambda: Fail(valError))
      .then(lambda: OK(40))
      .catch(lambda err: Fail(synError)))

    self.assertEqual(Fail(synError), attemptReraise)

    attemptCatchOK = (OK(10)
      .then(lambda: OK(20))
      .then(lambda: OK(40))
      .catch(lambda err: OK("123")))

    self.assertEqual(OK(40), attemptCatchOK)

 
  #def testScoping(self):
  #  x = []  
  #  for i in range(1, 5):  
  #    x.append(lambda z: "%d" % i + z)
  # 
  #  testList = [ x[d]("banza") for d in range(0,4) ] 
  #  self.assertEqual(testList, ['1banza','2banza','3banza','4banza'])

