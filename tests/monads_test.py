import unittest
from substance.monads import *
from collections import namedtuple

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

  def testTryThenIfBool(self):
    valError = ValueError()
    self.assertEqual(OK(10).thenIfBool(lambda *x: OK(20), lambda *x: Fail(valError)), Fail(valError))
    self.assertEqual(OK(True).thenIfBool(lambda *x: OK(20), lambda *x: Fail(valError)), OK(20))
    self.assertEqual(OK(False).thenIfBool(lambda *x: OK(20), lambda *x: Fail(valError)), Fail(valError))
    self.assertEqual(Fail(valError).thenIfBool(lambda *x: OK(20), lambda *x: OK(20)), Fail(valError))
    self.assertEqual(OK(True).thenIfTrue(lambda *x: OK(10)), OK(10))
    self.assertEqual(OK(True).thenIfFalse(lambda *x: OK(10)), OK(True))
    self.assertEqual(OK(False).thenIfTrue(lambda *x: OK(10)), OK(False))
    self.assertEqual(OK(False).thenIfFalse(lambda *x: OK(10)), OK(10))

  def testTryThenIfNone(self):
    self.assertEqual(OK(10).thenIfNone(lambda *x: OK(20)), OK(10))
    self.assertEqual(OK(None).thenIfNone(lambda *x: OK(20)), OK(20))

  def testTryBindIf(self):
    valError = ValueError()
    self.assertEqual(OK(True).bindIf(lambda *x: OK(10), lambda *x: Fail(valError)), OK(10)) 
    self.assertEqual(OK(False).bindIf(lambda *x: OK(10), lambda *x: Fail(valError)), Fail(valError)) 
    self.assertEqual(OK(True).bindIfTrue(lambda *x: OK(10)), OK(10))
    self.assertEqual(OK(True).bindIfFalse(lambda *x: OK(10)), OK(True))
    self.assertEqual(OK(False).bindIfTrue(lambda *x: OK(10)), OK(False))
    self.assertEqual(OK(False).bindIfFalse(lambda *x: OK(10)), OK(10))

  def testTryCatchError(self):
    valError = ValueError()
    synError = SyntaxError()
    self.assertEqual(OK(True).catchError(ValueError, lambda *x: OK(10)), OK(True))
    self.assertEqual(OK(False).catchError(ValueError, lambda *x: OK(10)), OK(False))
    self.assertEqual(Fail(synError).catchError(ValueError, lambda e: OK(10)), Fail(synError))
    self.assertEqual(Fail(synError).catchError(SyntaxError, lambda e: OK(10)), OK(10))

  def testFunctions(self):
    self.assertEqual(defer(lambda x,y: x+y, 1, 2)(), 3)
    self.assertEqual(defer(lambda x,y: x+y)(1, 2), 3)
    valError = ValueError()
    self.assertEqual(failWith(valError)(), Fail(valError))
    self.assertEqual(failWith(valError)(1,2,3,4), Fail(valError))

    def fa(x):
      return x+2
    def fb(x):
      return x+1
    def fc(acc, x):
      return acc+x

    self.assertEqual(compose(fa, fb)(1), fa(fb(1)))
    self.assertEqual(fold(fc, [1,2,3,4], 0), 10)

  def testMapM(self):
    self.assertEqual(mapM(Try, lambda x: OK(x+x), [1,2,3,4]), OK([2,4,6,8]))

    testList = []
    self.assertEqual(mapM_(Try, lambda x: OK(testList.append(x+x)), [1,2,3,4]), OK([1,2,3,4]))
    self.assertEqual([2,4,6,8], testList)

    self.assertEqual(OK([1,2,3,4]).mapM(lambda x: OK(x+x)), OK([2, 4, 6, 8]))

    testList = []
    self.assertEqual(OK([1,2,3,4]).mapM_(lambda x: OK(testList.append(x+x))), OK([1,2,3,4]))
    self.assertEqual([2,4,6,8], testList)

  def testSequence(self):
    self.assertEquals(sequence(Try, [OK(1),OK(2),OK(3),OK(4)]), OK([1,2,3,4]))
    self.assertIsInstance(sequence(Try, [OK(1),OK(2),OK(3),Fail(ValueError())]), Fail)

    self.assertEquals(Try.sequence([OK(1),OK(2),OK(3)]), OK([1,2,3]))
    self.assertIsInstance(Try.sequence([OK(1),Fail(ValueError()),OK(3)]), Fail)
    
  def testUnshiftM(self):
    self.assertEquals(unshiftM(Try, OK([2,3]), OK(1)), OK([1,2,3]))

  def testFlatten(self):
    self.assertEqual(['a','b','c','d','e','f'], flatten([['a','b'], ['c','d'], ['e','f']]))

