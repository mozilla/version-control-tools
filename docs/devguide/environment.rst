.. _devguide_environment:

==================================================
Creating and Maintaining a Development Environment
==================================================

Requirements
============

To create a development and test environment, you'll need Linux or OS X
host operating system. **Windows is currently not supported.**

You will need Python 2.7.

Many components use `Docker <https://www.docker.com/>`_. You'll need
Docker to perform many tasks. Functionality requiring Docker should be
skipped if Docker is not available.

.. warning::

   There are known issues with Python 2.7.9 and our Docker setup. If
   the underlying problem is detected, you should see a warning.

   To install a different version of Python, we recommend using
   `pyenv <https://github.com/yyuu/pyenv>`_. Once installed, activate
   an appropriate Python version in your shell by running
   ``pyenv local 2.7.8`` or similar.

Aside from the base requirements, the development and testing
environment should be fully self-contained and won't pollute your
system.

If you are on Windows or want to create a fully-isolated environment,
the Vagrant configuration used by :ref:`Jenkins <devguide_jenkins>`
provides a fully capable environment.

.. _devguide_create_env:

Creating and Updating Your Environment
======================================

Development and testing requires the creation of a special environment
containing all the prerequisites necessary to develop and test. This
is accomplished by running the following command::

   $ ./create-test-environment

.. tip::

   You should periodically run ``create-test-environment`` to ensure
   everything is up to date. (Yes, the tools should do this
   automatically.)

Activating an Environment
=========================

Once you've executed ``create-test-environment``, you'll need to
*activate* it so your current shell has access to all its wonders::

   $ source venv/bin/activate

boot2docker
===========

If you are running OS X and have boot2docker installed to run Docker
containers, you may want to increase the amount of memory available
to the boot2docker VM.

Run the following to see how much memory is currently allocated to
boot2docker::

   $ boot2docker config | grep Memory
   2048

The default is ``2048`` (megabytes). **We recommend at least 4096
MB.**

To adjust the amount of memory allocated to boot2docker, run the
following::

   $ VBoxManage modifyvm boot2docker-vm --memory 4096

Alternatively, if you haven't created a boot2docker VM yet, define the
memory allocation when you create it::

   $ boot2docker init --memory=4096
