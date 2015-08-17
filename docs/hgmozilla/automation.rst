.. _hgmozilla_automation:

=============================
Using Mercurial in Automation
=============================

Are you looking to consume Mercurial as part of an automated system? This
article attempts to answer common questions and to suggest best practices.

Best Practices
==============

Read the Scripting Help Topic
-----------------------------

``hg help scripting`` (introduced in Mercurial 3.5) gives a Mercurial
generic overview of how machines should consume Mercurial.

Get Design and Code Review from Someone Who Knows Mercurial
-----------------------------------------------------------

Before you write any code or deploy anything, it might be a good idea to
get design review or code review from someone who knows Mercurial.

Pop in ``#vcs`` on ``irc.mozilla.org`` or send an email to
`dev-version-control@lists.mozilla.org <mailto:dev-version-control@lists.mozilla.org>`_.

Consider Using the Command Server
---------------------------------

Mercurial has a *command server* mode where a persistent ``hg`` process is
created and individual commands are dispatched to the server one at a time.

There exists client libraries for communicating with this command server
`python-hglib <https://pypi.python.org/pypi/python-hglib>`_ is the Python
client and it can be installed via ``pip install python-hglib``.

Use of the command server is preferred over direct ``hg`` process invocation
because:

1. It is faster.
2. A written client API will handle dispatching and parsing responses
   automatically, freeing you up to write meaningful code.

Python + hg process startup overhead is non-trivial (~50 ms). If you are
performing many Mercurial commands, use of the command server could have a
profound impact on performance.

Use Templates
-------------

Most Mercurial commands accept a ``--template/-T`` argument to control how
output is formatted. You should use this capability when calling commands
to ensure output is exactly how you intend. This can often result in making
the output easier for machines to parse.

.. tip::

   Use ``-T json`` to produce JSON output from commands.

Add --traceback to All Commands
-------------------------------

In the rare case Mercurial crashes, it is valuable to have crash information
to help with debugging. Adding ``--traceback`` to all commands will have
Mercurial print a stack trace when it crashes.

As an alternative to adding ``--traceback`` to every command, add the following
to your hgrc::

   [ui]
   traceback = on

Always Check Exit Codes
-----------------------

**Always** check that the exit code from ``hg`` commands is what is expected
(probably ``0``).

Specify an Explicit hgrc
------------------------

Mercurial will automatically inherit the system-wide and per-user ``hgrc``
files. This can have unintended consequences, such as the enabling of an
extension or defining of specific user credentials.

When invoking the ``hg`` command, set the ``HGRCPATH`` environment variable to
that of a known good config file.

.. tip::

   To disallow loading of an external hgrc file, set ``HGRCPATH`` to the value
   ``/dev/null``.

.. note::

   If executing from within a Mercurial repository, the ``hg`` process will
   automatically load the ``.hg/hgrc`` file. This is not always intended,
   especially if you are running commands that don't interact with a specific
   repository.

   To prevent this, execute your ``hg`` process from outside any Mercurial
   repository. e.g. ``/``.

   You can always pass ``-R /path/to/repo`` to have Mercurial operate on a
   specific repository - you don't need to have ``cwd`` be from within the
   repository.

Other Tips
==========

Debugging
---------

When debugging Mercurial commands, consider adding ``--verbose`` or ``--debug``
to the command invocation to get Mercurial to print more information about what
it is doing. This output can be especially when reporting bugs.

Like ``--traceback``, these options can be enabled via ``hgrc`` files::

   [ui]
   debug = True
   verbose = True
