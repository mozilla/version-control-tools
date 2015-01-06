.. _testing:

=======
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

  $ ./run-mercurial-tests.py -j8

Obtain code coverage results (makes tests run slower)::

  $ ./run-mercurial-tests.py --cover

Test a single file::

  $ ./run-mercurial-tests.py path/to/test.t

Run a test in debug mode::

  $ ./run-mercurial-tests.py -d path/to/test.t

Run tests against all supported Mercurial versions::

  $ ./run-mercurial-tests.py --all-versions

Run tests with a specific Mercurial installation::

  $ ./run-mercurial-tests.py --with-hg=/path/to/hg

Writing New Tests
=================

There are 3 flavors of tests recognized by ``run-mercurial-tests.py``:

1. Mercurial .t tests
2. Mercurial .py tests
3. Python unit tests

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

As for the contents of test files, look at an existing test for
inspiration.

Mercurial ``.t`` tests are highly preferred for anything testing
Mercurial.

Jenkins Continuous Integration
==============================

This repository is continuously tested via Jenkins. You can find the
canonical Jenkins job at
https://ci.mozilla.org/job/version-control-tools/.

The Jenkins test environment is configured such that it can be executed
by anyone, anywhere.

The ``testing/jenkins`` directory contains everything you need to
reproduce the canonical Jenkins job.

In that directory are the following files:

Vagrantfile
   Defines the virtual machine used to run test automation.
run-main.py
   A script used to run the tests. This is what you'll configure your
   Jenkins job to execute to run the job.
run.sh
   Main script that runs inside the virtual machine to run test
   automation. This is invoked by ``run-main.py``.

Configuring Jenkins
-------------------

The Jenkins build only needs to consist of a single step: a shell script
that executes::

   testing/jenkins/run-main.py

For post-build actions, you have a number of options.

You can *Publish Cobertura Coverage Report* by using
``**/coverage/coverage.xml`` for the *Cobertura xml report pattern*.

You can *Publish JUnit test result report*s by using
``coverage/results.xml`` as the *Test Reports XML* value.

You can *Publish coverage.py HTML reports* by setting
``coverage/html`` as the *Report directory*.

You can *Publish HTML Reports* containing the generated Sphinx
documentation by setting ``sphinx-docs/html`` as the *HTML directory to
archive* and setting the *Index Page* to ``index.html``.
