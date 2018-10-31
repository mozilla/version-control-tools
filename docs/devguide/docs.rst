.. _devguide_docs:

=============================
Contributing to Documentation
=============================

Improvements to the documentation in this repository are very welcome!

Building Documentation Locally
==============================

To build documentation locally, you will need a Python environment.

Assuming you already have a copy of the source repository, run the
following commands to activate the environment for building the docs::

   $ ./create-environment docs
   $ source venv/docs/bin/activate

Then to build the docs::

   $ make -C docs html

You can then open docs/_build/html/index.html in your web browser to
navigate the generated docs.

Submitting Patches
==================

If you have a change to the docs that you would like to be incorporated,
please follow the :ref:`regular contributing guide <devguide_contributing>`
to learn how to submit patches.

Commit messages for documentation-only changes should be prefixed with
``docs:``.
