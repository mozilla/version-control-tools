.. _vcssync_development:

=================
Development Guide
=================

Creating a Development and Testing Environment
==============================================

From a fresh ``version-control-tools`` checkout, run the following to create
a development and testing environment::

   $ ./create-environment vcssync

Then activate the environment in your shell via::

   $ source activate venv/vcssync/bin/activate

Running Tests
=============

To run the vcssync tests, run::

   $ ./run-tests -j4
