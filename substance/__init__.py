import sys
from substance.command.main import (Substance)

def cli():
  subst = Substance()
  subst.execute(sys.argv)
