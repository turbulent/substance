import unittest
import tempfile
import sys
import pprint

class TestBase(unittest.TestCase):

  tempFiles = []
  tempDirs = []

  @classmethod
  def addTemporaryFile(cls):
    tempFile = tempfile.NamedTemporaryFile()
    cls.tempFiles.append(tempFile)
    return tempFile

  @classmethod
  def addTemporaryDir(cls):
    tempDir = tempfile.mkdtemp()
    cls.tempDirs.append(tempDir)
    return tempDir

  @classmethod
  def clearTemporaryDirs(cls):
    for x in cls.tempDirs:
      Shell.nukeDirectory(x)

  @classmethod
  def clearTemporaryFiles(cls):
    for x in cls.tempFiles:
      x.close()
 
  @staticmethod
  def raiser(e):
    raise e
