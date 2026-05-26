.. _devguide_docs:

=============================
Contributing to Documentation
=============================

Improvements to the documentation in this repository are very welcome!

Building Documentation Locally
==============================

To build documentation locally, you will need a Python environment
with the ``docs`` dependency group installed. The group is declared
in ``pyproject.toml`` and is materialised with
`uv <https://docs.astral.sh/uv/>`_.

Assuming you already have a copy of the source repository, run the
following commands to create and activate the environment::

   $ uv sync --only-group docs --python 3.9
   $ source .venv/bin/activate

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
