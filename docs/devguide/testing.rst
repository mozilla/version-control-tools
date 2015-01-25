.. _devguide_testing:

=======
Testing
=======

Methodology
===========

Testing the code in this repository is taken very seriously. We want
to facilitate confidence that any change will have the intended
side-effects and won't regress behavior. We do this by providing a
testing framework that is comprehensive and robust.

We currently support the following flavors of tests:

1. Python unit tests
2. Mercurial *t tests*
3. Mercurial .py tests

The test driver is responsible for identifying which flavor a particular
file is.

Many tests interact with services running locally, commonly inside
Docker containers. For example, MozReview tests create Bugzilla, Pulse,
and Mercurial servers. **Running actual services is encouraged over
mocking.**

Running
=======

Tests are executed by running the following in an *activated*
:ref:`environment <devguide_create_env>`::

   $ ./run-mercurial-tests.py

To see help on options that control execution::

   $ ./run-mercurial-tests.py --help

Unknown script arguments will be proxied to Mercurial's ``run-tests.py``
testing harness.

Common tasks are described below.

Run all tests, 8 at a time::

  $ ./run-mercurial-tests.py -j8

Obtain code coverage results (makes tests run slower)::

  $ ./run-mercurial-tests.py --cover

Test a single file::

  $ ./run-mercurial-tests.py path/to/test.t

Run all tests in a directory::

  $ ./run-mercurial-tests.py hgext/reviewboard

Run a test in debug mode (see progress, interact with a debugger)::

  $ ./run-mercurial-tests.py -d path/to/test.t

Run tests against all supported Mercurial versions::

  $ ./run-mercurial-tests.py --all-versions

Run tests with a specific Mercurial installation::

  $ ./run-mercurial-tests.py --with-hg=/path/to/hg

Authoring Tests
===============

Test File Naming
----------------

Mercurial ``.t`` and ``.py`` tests will be automatically discovered from
the following directories:

* ``hgext/*/tests/``
* ``hghooks/tests/``

Mercurial test filenames must be prefixed with ``test-``. e.g.
``test-foo.t``.

Python unit tests will be discovered from the following directories:

* ``pylib/**``

Python unit test filenames must be prefixed with ``test``. e.g.
``test_foo.py``.

To write a new test, simply put the test file in one of the
aforementioned directories and name it so that it will be discovered. If
you run ``run-mercurial-tests.py path/test/test`` and the specified
filename wouldn't get discovered, an error will be raised saying so.

Choice of Test Flavor
---------------------

Mercurial `t tests <http://mercurial.selenic.com/wiki/WritingTests>`_
are recommended for most tests.

Mercurial *t tests* are glorified shell scripts. Tests consist of a
series of commands that will be invoked in a shell. However, they are
much more than that. Expected output from commands is captured inline
in the ``.t`` file. For example:

.. code::

   $ hg push
   pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
   searching for changes
   remote: adding changesets
   remote: adding manifests
   remote: adding file changes
   remote: added 1 changesets with 1 changes to 1 files

If the expected output differs from actual, the Mercurial test harness
will print a diff of the changes.

*.t tests* are very useful for testing the behavior of command line
programs.

Unless you are testing a headless Python module, you should probably
be writing *t tests*.

Python APIs and Helper Scripts
------------------------------

Tests often want to instantiate services and interact with them. To
facilitate this, there are various Python APIs and helper scripts.

The Python APIs are all available as part of the
:doc:`vcttesting package </vcttesting/modules>`. There is typically
a subpackage or module for each service you may want to interact with.

To facilitate testing from *t tests*, there are various command line
tools for interacting with specific services. For example, the
``mozreview`` tool allows you to start up and stop ``mozreview``
instances. The ``bugzilla`` tool allows you to perform common
actions against a Bugzilla instance, such as create a bug.

These APIs and scripts exist only to support testing. Their APIs and
arguments are not considered stable. They should not be relied on
outside the context of the testing environment.

The CLI tools all use *mach* for command dispatching. Simply run
``<tool> help`` to see a list of what commands are available.
