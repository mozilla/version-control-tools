========================
bugzilla.mozilla.org fig
========================

This directory contains a Fig definition for running a
bugzilla.mozilla.org (BMO) installation as a cluster of Docker
containers.

To start up Bugzilla, run::

   fig up

You should see a BMO database node and BMO web node spin up.

Apache should be listening on a randomly assigned local port. To find
out the port number, run ``fig ps`` and the port number should be
printed.

To run in daemon mode::

   fig up -d
