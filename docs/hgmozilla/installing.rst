.. _hgmozilla_installing:

====================
Installing Mercurial
====================

Having a modern Mercurial installed is important. Features, bug fixes,
and performance enhancements are always being added to Mercurial.
Staying up to date on releases is important to getting the most out of
your tools.

.. note::

   Mercurial has a strong committment to backwards compatibility.

   If you are scared that upgrading will break workflows or command
   behavior, don't be. It is very rare for Mercurial to break backwards
   compatibility.

Recommended Versions
====================

Mozilla recommends running the latest stable release of Mercurial.

Mercurial makes a major *X.Y* release every three months, typically around
the first of the month. Release months are February, May, August, and
November. A *X.Y.Z* point release is performed each month after or as
needed (if a severe issue is encountered).

Versions to Avoid
-----------------

Mercurial versions older than 3.2.3 should be avoided due to a security
issue (CVE-2014-9390) impacting Windows and OS X users.

Mercurial versions older than 3.x should be avoided because they are
old, slow, and contain known bugs. Also, it is difficult to maintain
extension compatibility with them.

Mercurial 3.0 through 3.1.1 contained a significant performance
regression that manifests when performing certain repository operations,
such cloning or pulling several thousand changesets. **If you use these
versions with the Firefox repository, you are going to have a bad
time.** The regression was fixed in Mercurial 3.1.2.

Installing on Windows
=====================

If you are a Firefox developer, you should install Mercurial indirectly
through `MozillaBuild <https://wiki.mozilla.org/MozillaBuild>`_.

If you are not a Firefox developer, download a Windows installer
`direct from the Mercurial project <http://mercurial.selenic.com/downloads>`_.

Installing on OS X
==================

Mercurial is not installed on OS X by default. You will need to install
it from a package manager or install it from source.

Homebrew
--------

Homebrew typically keeps their Mercurial package up to date. Install
Mercurial through Homebrew by running::

  $ brew install mercurial

You may want to run ``brew update`` first to ensure your package
database is up to date.

MacPorts
--------

MacPorts typically keeps their Mercurial package up to date. Install
through MacPorts by running::

  $ port install mercurial

Installing on Linux, BSD, and other UNIX-style OSs
==================================================

The instructions for installing Mercurial on many popular distributions
are available on `Mercurial's web site <http://mercurial.selenic.com/downloads>`_.
However, many distros don't keep their Mercurial package reasonably
current. You often need to perform a source install.

Installing from Source
======================

Installing Mercurial from source is simple and should not be dismissed
because it isn't coming from a package.

Download a `source archive <http://mercurial.selenic.com/downloads>`_
from Mercurial. Alternatively, clone the Mercurial source code and check
out the version you wish to install::

  $ hg clone http://selenic.com/repo/hg
  $ cd hg
  $ hg up 3.2.4

Once you have the source code, run ``make`` to install Mercurial::

  $ make install

If you would like to install Mercurial to a custom prefix::

  $ make install PREFIX=/usr/local
  $ make install PREFIX=/home/gps

.. note::

   Mercurial has some Python C extensions that make performance-critical
   parts of Mercurial significantly faster. You may need to install a
   system package such as ``python-dev`` to enable you to build Python C
   extensions.

.. tip::

   Are you concerned about a manual Mercurial install polluting your
   filesystem? Don't be.

   A Mercurial source install is fully self-contained. If you install to
   a prefix, you only need a reference to the ``PREFIX/bin/hg`` executable
   to run Mercurial. You can create a symlink to ``PREFIX/bin/hg`` anywhere
   in ``PATH`` and Mercurial should *just work*.

Verifying Your Installation
===========================

To verify Mercurial is installed properly and has a basic configuration
in place, run::

  $ hg debuginstall

If it detects problems, correct them.
