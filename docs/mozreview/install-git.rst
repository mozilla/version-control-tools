.. _mozreview_install_git:

================================
Configuring Git to Use MozReview
================================

Submitting patches to MozReview requires pushing commits to a special
code review repository (similar to how GitHub Pull Requests are
initiated by pushing commits to GitHub).

Because various repositories are canonically hosted in Mercurial, the
special code review repositories are Mercurial - not Git - repositories.


Installing Mercurial
====================

Mercurial is used under the covers when submitting to MozReview. See
:ref:`hgmozilla_installing` for instructions on installing Mercurial.

.. important::

   A modern version of Mercurial is **required** to submit to MozReview.

   Please verify your installed Mercurial version against what is listed
   at :ref:`hgmozilla_installing` before continuing.

Installing git-cinnabar
=======================

`git-cinnabar <https://github.com/glandium/git-cinnabar>`_ allows Git
to fetch from and push to Mercurial repositories. Use of git-cinnabar is
**required** to submit Git commits to MozReview.

Install git-cinnabar by following the directions on its GitHub project
page.

.. important::

   git-cinnabar 0.3.1 (released 2016-01-16) or newer is required.

Installing MozReview Git Tools
==============================

Git support for MozReview requires a handful of support tools and libraries.
All the code (except for Git, Mercurial, and git-cinnabar) are located
in the
`version-control-tools <https://hg.mozilla.org/hgcustom/version-control-tools>`_
repository. You will need to clone this repository to your local machine.

If you have a Firefox repository cloned, run ``mach mercurial-setup`` from it
and it will clone version-control-tools to ``~/.mozbuild/version-control-tools``.

To clone version-control-tools manually::

   $ hg clone https://hg.mozilla.org/hgcustom/version-control-tools

   OR

   $ git clone hg::https://hg.mozilla.org/hgcustom/version-control-tools

.. note::

   We'll use ``vct`` as an abbreviation for *version-control-tools*.

Next, tell Git to find Git commands located in the ``git/commands`` directory
of this repository by updating your ``PATH`` environment variable (likely
in your ``~/.profile`` or similar shell init script):

   $ export PATH=/path/to/vct/git/commands:$PATH

.. tip::

   You likely updated your ``PATH`` variable as part of installing git-cinnabar.
   You should update the same thing to register version-control-tool's Git
   commands.

Configuring Access Credentials
==============================

You'll need to define Bugzilla access credentials to communicate with MozReview.
These are defined as part of the Git configuration file.

You can configure them globally via ``git config``::

    $ git config --global bz.username someone@example.com
    $ git config --global bz.apikey as3r123hj325hjld3

Or if you don't wish to define these credentials globally,
``git mozreview configure`` (described below) will record them in your
``.git/config``.

.. note::

   You can generate or obtain an already-generated API Key from
   https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey.

   It is recommended to use ``git`` or ``git-mozreview`` as the name
   of the API Key.

.. important::

   Logging into MozReview will create a Bugzilla API Key named
   ``mozreview``. This API Key has limited permissions and isn't
   suitable for use by Git.

MozReview also currently requires a nickname to be specified. This is
used as a label for commits series. It will likely go away sometime.
It is recommended to use your IRC nickname if you have one. To configure
this nickname::

   $ git config --global mozreview.nickname mynick

Configuring a Repository to Submit to MozReview
===============================================

Each local Git repository wishing to submit patches to MozReview will
need to be configured for MozReview integration. Configuring a
repository is simple::

   $ git mozreview configure

If you manually configured global settings above, this command should
complete automatically. If not, it will prompt you for e.g. your
Bugzilla access credentials.

By default, ``git mozreview configure`` will configure the ``review``
Git remote. See ``git mozreview configure help`` on how to change the
default remote name.

Once ``git mozreview configure`` is run, you should now be able to
use ``git mozreview push`` to submit commits to MozReview for
review.

Proceed to :ref:`mozreview_commits` for more info.
