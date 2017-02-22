# macOS Installation Guide

## Instructions

1. Download [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads) 5.1.x+ and install the [VM Extensions](http://download.virtualbox.org/virtualbox/5.1.6/Oracle_VM_VirtualBox_Extension_Pack-5.1.6-110634.vbox-extpack).

2. Make sure Xcode CLI is installed

        $ xcode-select --install

3. Ensure homebrew is installed

        $ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

4. Install homebrew python (the python interpreter which ships with macOS is unsuitable for substance)

        $ brew install python

5. Ensure pip is up to date

        $ pip install -U pip

6. Install subwatch alpha

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@1.0

7. Install substance alpha

        $ pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@0.9a1

