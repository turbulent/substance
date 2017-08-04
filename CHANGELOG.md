# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Changed
- All Python source code now adheres to the [PEP 8 -- Style Guide for Python
  Code](https://www.python.org/dev/peps/pep-0008/).

### Fixed
- Crash in `hatch` under Mac OS X due to BSD tar implementation.
- Crash when running `substance engine`.
- Crash in `hatch` when supplying values containing slash (`/`) characters.

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
