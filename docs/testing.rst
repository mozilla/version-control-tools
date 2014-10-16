.. _testing:

Testing
=======

This repository contains extensive tests of the functionality therein.
To run the tests, you'll need a Linux or OS X install. You can always
obtain a Linux install by running a virtual machine.

Testing requires a special Python environment. To create this
environment::

  $ ./create-test-environment
  $ source venv/bin/activate

Then, launch the tests::

   $ ./run-mercurial-tests.py

To see help on options that control execution::

   $ ./run-mercurial-tests.py --help

Unknown script arguments will be proxied to Mercurial's ``run-tests.py``
testing harness.

Common tasks are described below.

Run all tests, 8 at a time::

  $ ./run-mercurial-tests -j8

Obtain code coverage results (makes tests run slower)::

  $ ./run-mercurial-tests --cover

Test a single file::

  $ ./run-mercurial-tests path/to/test.t

Run a test in debug mode::

  $ ./run-mercurial-tests -d path/to/test.t

Run tests against all supported Mercurial versions::

  $ ./run-mercurial-tests --all-versions

Run tests with a specific Mercurial installation::

  $ ./run-mercurial-tests --with-hg=/path/to/hg
