# Linux installation guide

Make sure you are running a 64-bit Linux distribution. 32-bit is NOT supported. Substance has been tested on Mint, Ubuntu, and Arch Linux.

## Instructions


1. Install latest VirtualBox. Also install extension pack (separate download).
   Make sure `VBoxManage` is in your `PATH` variable.
2. Install the following software using your package manager. Of course,
   depending on the distribution, the package names may slightly vary (but you
   will usually find a proper equivalent):
   1. `git`
   2. `build-essential`
   4. `libffi-devel`
   5. `openssl-devel`
3. Make sure to have Python 2 available. On some distributions (like Ubuntu
   14.04), this is the default Python interpreter, which means you can use
   `python` and `pip`. On other, more state-of-the-art distributions (like
   Arch), you need to install a separate `python2` package and use the commands
   `python2` and `pip2` for the rest of this guide. Also install `python-devel`
   or `python2-devel`, depending on your distribution.
4. Self-update pip:

        $ pip install -U pip

5. Install `subwatch` alpha via `pip` by running the command

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@1.0

6. Install `substance` alpha via `pip` by running the command

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@0.10

