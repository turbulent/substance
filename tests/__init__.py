import unittest
import tempfile
import sys

class TestBase(unittest.TestCase):

  tempFiles = []
  tempDirs = []
  def addTemporaryFile(self):
    tempFile = tempfile.NamedTemporaryFile()
    self.tempFiles.append(tempFile)
    return tempFile

  def addTemporaryDir(self):
    tempDir = tempfile.mkdtemp()
    self.tempDirs.append(tempDir)
    return tempDir

  def clearTemporaryDirs(self):
    for x in self.tempDirs:
      Shell.nukeDirectory(x)

  def clearTemporaryFiles(self):
    for x in self.tempFiles:
      x.close()

  def raiser(self, e):
    raise e
