=================================
Execution Environment For Jenkins
=================================

This directory contains the definition for an execution environment to
run the test automation for this repository under the Jenkins continuous
integration system.

This directory is optimized for turn-key use with Mozilla's Jenkins
installation at https://ci.mozilla.org/job/version-control-tools/.
However, anybody should be able to use this environment under Jenkins.

This directory contains the following files:

Vagrantfile
   Defines the virtual machine used to run test automation
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

Known Issues
============

The code in ``run-main.py`` to destroy the Vagrant VM after job failure
is a bit hacky. It should ideally be removed and more robust checks be
added inside the VM.
