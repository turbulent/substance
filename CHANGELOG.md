# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2019-01-20

# Feature
- Add the ability to use other orchestrators within the your subenv
- Add the dockwrkr orchestrator as the default one
- Add docker-compose as a new generation orchestrator

# Bug fix
- Fixed bug with lru_cache and lists preventing proper memoization of list args
- Fixed bug with legacy < 1.0 env template that referred to iteritems()
- Fixed bug with dockwrkr where specifying an 'email' for a registry caused a deprecation error.
- Fixed bug within WSL when non-memoize paths were resolved as outer paths but were already proper windows paths.

## [1.0.0] - 2019-01-12

# Features
- Substance now requires Python3.
- Added proper support for subsystem paths for Windows Subsystem for Linux (WSL)
- Upgrade unison integration to use v2.51.2 (OCaml 4.07.1)

# Changes

- Downgraded unox (unison-fsmonitor) to use macfsevents instead of watchdog for performance
- Virtualbox driver will now use an existing host interface if one that is configured properly exists

# Fixed
- Fixed a bug where running without a TTY (headless) would cause fatal errors
- Fixed a bug under Virtualbox 6.0 where host-only interfaces would not be detected right
- Fixed a bug where box records in the local substance database would be duplicate
- Fixed a bug where box records were not properly removed

## [0.14.1] - 2017-11-09

### Fixed
- `substance cleanup` no longer requires an active subenv to operate.

## [0.14.0] - 2017-11-09

### Added
- New CLI command: `substance cleanup`, remove unused images and containers.

### Fixed
- SSH connection will no longer give up during the boot process.
- The DHCP range used for the substance hoif will now start at a higher number to prevent gateway conflicts.
- The boot process of substance boxes will no longer try to mount shared folders even if none are configured.
- `substance switch` will no longer fail when inexistent linked containers are configured in the subenv.

### Changed
- `substance switch` will no longer force a pull on all images and only login once instead.
- The default box is now a substance version constants instead of a configuration option.
- Default Box is now turbulent/substance-box:0.7.
- SSH handling now properly uses and forwards SSH agents to box.
- The SSH privateKey/publicKey substance configuration options are now removed.


## [0.13.0] - 2017-08-08
### Added
- `substance sync` now accepts a sub-path argument to limit scope of sync.

### Changed
- All Python source code now adheres to the [PEP 8 -- Style Guide for Python
  Code](https://www.python.org/dev/peps/pep-0008/).

### Fixed
- Crash in `hatch` under Mac OS X due to BSD tar implementation.
- Crash when running `substance engine` to get a list of sub-commands.
- Crash in `hatch` when supplying values containing slash (`/`) characters.
- `-i` option in `substance sync` is now guaranteed to work as expected.

## [0.12.1] - 2017-06-20
### Fixed
- Timeout error under macOS when pulling a box from bintray.com

## [0.12.0] - 2017-06-14
### Added
- `hatch` now supports downloading templates from tarballs
- `hatch` now defaults to GitHub tarball archives when using short template
  names
- `hatch` now supports new `pre-script` and `post-script` elements in
  `hatch.yml`.
### Changed
- Aborted Python 3 support. We will revisit this feature when Python 3 is the
  default on the most-used Linux distributions and Mac OS X Homebrew.

## [0.11.0] - 2017-06-12
### Added
- Python 3.x support!
- Comprehensive user documentation generated with Sphinx
### Changed
- Bintray.com is now used for hosting virtual machine images publicly.
- `subwatch` is no longer a required dependency of Substance.
### Fixed
- `sync` crash under macOS with Python 2.7.13

## [0.10.1] - 2017-05-09
### Fixed
- `hatch` wizard now uses the `readline` module whenever available.
- `hatch` replacements now properly work under Mac OS X.
- `hatch` now warns when running in non-empty directory.
- `hatch` now only runs replacements on files contained in the template.
- `expose` for ports <= 1024 now properly work under Windows Cygwin.

## [0.10] - 2017-05-05
### Added
- `hatch` command for generating code from an external git-hosted template.
- `expose` command for easily setuping SSH port-forwarding.
- Ability to use SSH Agent keys when connecting to the engine via SSH.

### Fixed
- Wrong error message printed if alias command returns non-zero exit code.
- Fixed incompatibility with recent VirtualBox version.

## [0.9a1] - 2017-02-01
### Added
- Official Linux 64-bit support
- Support for engine-defined project aliases
- New `substance aliases` command
- Engine can be specified on any command using `-e` now.
- Add `-i` option to `substance sync` for easy fix with unison failures.
- More detailed documentation

### Changed
- `substance switch` now restarts containers by default (disable with `--keep-containers`).

## [0.8a4] - 2017-02-01
### Fixed
- sync crash on Windows

## [0.8a3] - 2017-01-31
### Fixed
- pip install on 0.8a2 was broken.

## [0.8a2] - 2017-01-31
### Fixed
- Make sure proper `docker login` is performed on a `substance switch`.

## [0.8a1] - 2017-01-31
### Added
- Official Windows support under Cygwin-64.
- New mode of sync: unison
- Substance box upgrade to 0.6 to have unison packed in.
- `substance launch` will not automatically start containers if an active environment is set.
