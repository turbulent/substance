# macOS Installation Guide

## Instructions

1. Download [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads) 5.1.x+ and install the VM Extensions.

2. Make sure Xcode CLI is installed

        $ xcode-select --install

3. Ensure homebrew is installed

        $ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

4. Install homebrew python (the python interpreter which ships with macOS is unsuitable for substance)

        $ brew install python

5. Make sure that running the command `python` executes the one under `/usr/local/bin`:

        $ which python
        /usr/local/bin/python
        $ which pip
        /usr/local/bin/pip

   If this command outputs some other path like `/usr/bin/python`, you're in trouble. You should add the following line to your `.profile` or `.bash_profile` file:

        export PATH=/usr/local/bin:$PATH

   Start a new terminal, and that should fix the issue (test it with the `which` commands above).

6. Ensure pip is up to date

        $ sudo pip install -U pip

7. Install `subwatch`:

        $ sudo pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@1.0

8. Install `substance` (replace `[VERSION]` with the latest stable version or `master`):

        $ sudo pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@[VERSION]

