import subprocess
import os
import random
import string
import readline # This is important, we need to import this to make raw_input nicer
from substance import (Command)
from substance.logs import (logging)
from substance.config import (Config)

logger = logging.getLogger(__name__)

class Hatch(Command):

  def getUsage(self):
    return "substance hatch [options] TEMPLATE REF"

  def getHelpTitle(self):
    return "Create a new project based on a git template"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    tpl = self.getArg(0)
    if not tpl:
      return self.exitError("You MUST provide a template name or git repository URL!")
    ref = self.getArg(1)
    if not ref:
      return self.exitError("You MUST provide a version or git ref for the template!")

    if not tpl.startswith('ssh://') and not tpl.startswith('https://') and not tpl.startswith('file://'):
      tpl = 'ssh://git@gitlab.turbulent.ca:6666/templates/%s.git' % tpl

    print "You are about to hatch a new project in the current working directory."
    print "  Template used: %s" % tpl
    print "  Ref (version): %s" % ref
    print "  Path         : %s" % os.getcwd()

    if not self.confirm("Are you SURE you wish to proceed?"):
      return self.exitOK("Come back when you've made up your mind!")

    print "Downloading template archive..."
    if self.proc(['git', 'archive', '-o', 'tpl.tar.gz', '--remote=' + tpl, ref]):
      return self.exitError('Could not download template %s@%s!' % (tpl, ref))

    print "Extracting template archive..."
    if self.proc(['tar', '-xf', 'tpl.tar.gz']):
      return self.exitError('Could not extract template archive!')

    print "Cleaning up template archive..."
    if self.proc(['rm', 'tpl.tar.gz']):
      return self.exitError('Could not unlink temporary template archive!')

    # At this point, we have all the files we need
    hatchfile = os.path.join('.substance', 'hatch.yml')
    if os.path.isfile(hatchfile):
      config = Config(hatchfile)
      res = config.loadConfigFile()
      if res.isFail():
        return self.exitError("Could not open %s for reading: %s" % (hatchfile, res.getError()))
      vardefs = config.get('vars', {})
      # Autogenerate a secret
      chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
      variables = {
        '%hatch_secret%': ''.join(random.SystemRandom().choice(chars) for _ in range(32))
      }
      if vardefs:
        print "This project has variables. You will now be prompted to enter values for each variable."
        for varname in vardefs:
          val = ''
          required = vardefs[varname].get('required', False)
          default = vardefs[varname].get('default', '')
          description = vardefs[varname].get('description', '')
          while not val:
            val = raw_input("%s (%s) [%s]: " % (varname, description, default))
            if default and not val:
              val = default
            if not required:
              break
          variables[varname] = val

      summary = "\n".join(["  %s: %s" % (k, variables[k]) for k in variables.keys()])
      print "Summary: "
      print summary
      if not self.confirm("OK to replace tokens?"):
        return self.exitOK("Operation aborted.")

      print "Replacing tokens in files..."
      sed = "; ".join(["s/%s/%s/g" % (k, variables[k]) for k in variables.keys()])
      if self.proc(['find', '.', '-type', 'f', '-exec', 'sed', '-i', sed, '{}', '+']):
        return self.exitError("Could not replace variables in files!")

    print "Project hatched!"
    return self.exitOK()

  def proc(self, cmd, variables=None):
    logger.debug(subprocess.list2cmdline(cmd))
    return subprocess.call(cmd)

  def confirm(self, prompt):
    confirm = ''
    while confirm != 'Y':
      confirm = raw_input("%s (Y/n) " % prompt)
      if confirm == 'n':
        return False
    return True

