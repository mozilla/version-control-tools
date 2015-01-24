.. _devguide_testing:

=======
Testing
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
