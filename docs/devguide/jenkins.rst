.. _devguide_jenkins:

==============================
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
===================

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
