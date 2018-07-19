=============================
Mozilla Version Control Tools
=============================

This repository contains tools, extensions, hooks, etc to support version
control at Mozilla.

This repository contains the code that Mozilla uses in production to
power `hg.mozilla.org <https://hg.mozilla.org>`_,
`reviewboard.mozilla.org <https://reviewboard.mozilla.org>`_, and among
other sites and services.

The canonical repository is https://hg.mozilla.org/hgcustom/version-control-tools/

Most documentation exists in the ``docs/`` directory. It can be
`viewed online <https://mozilla-version-control-tools.readthedocs.io/en/latest/>`_
on Read the Docs.

If you are interested in getting in touch with the people who maintain
this repository, join ``#vcs`` in ``irc.mozilla.org``.

.. note:: A dev environment is needed for performing admin operations

    Before you can use any of the ansible playbooks for administration,
    you must have a development environment set up already. Best
    practice is to re-run ``./create-test-environment`` before using
    ``./deploy`` as your ansible entry point.
