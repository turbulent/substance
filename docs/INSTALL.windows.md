# Windows Installation Guide

Disclaimer: `substance` has only been tested on Windows 10 Pro 64-bit edition.
Installation on 32-bit Windows is NOT supported.

## Instructions

1. Install latest VirtualBox. Also install extension pack (separate download).
   Make sure VBoxManage is in your `PATH` environment variable (System ->
   Advanced System Settings -> Environment Variables -> Path -> add path to
   your VirtualBox installation directory).
2. Install Cygwin 64-bit. Here are the steps:
   1. Create a directory `C:\cygwin64` on your main drive. Create a subdirectory
      named "setup" inside that directory.
   2. Download `setup-x86-64.exe` from `https://www.cygwin.com/` and place it in
      `C:\cygwin64\setup`
   3. Double-click on `setup-x86-64.exe`, and perform the install. Keep the
      default location and make sure the following packages are selected:
      1. `mintty` (under "Shells")
      2. `git` (under "Devel")
      3. `gcc-core` (under "Devel")
      4. `python2` (under "Python")
      5. `python2-devel` (under "Python")
      6. `libffi-devel` (under "Libs")
      7. `openssl-devel` (under "Net")
   4. Optionally, you can create a shortcut to `setup-x86-64.exe` and add it to
      your Start menu; you can re-run the setup whenever you want to add or
      remove packages to your Cygwin install.
2. Launch Cygwin Terminal (`mintty`). All the magic happens from there!
3. Execute the command `python --version`. You should see an output like `Python 2.7.12`.
4. Make sure `pip` is installed and is upgraded to the latest version by running
   the commands

        $ python -m ensurepip
        $ pip install -U pip

5. Run `which python && which pip` to make SURE that you are running both
   executables from `/usr/bin`, NOT something like `C:\Python`!
6. Install `subwatch`:

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@1.0

7. Install `substance` (replace `[VERSION]` with the latest stable version or `master`):

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@[VERSION]

