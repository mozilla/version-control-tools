.. _cross_channel_architecture:

============
Architecture
============

.. toctree::
   :maxdepth: 2

   graph

Creating the cross-channel l10n repository consists of the following
architectural components:

#. Creating initial content
#. Updating content per push of original repository
#. Updating content for configuration changes

The intent is that the initial content creation is actually the same as
a configuration change that adds new files. One could choose to do otherwise,
but this is also a good way to ensure that the change handling configuration
changes won't just fail if the incoming content shows unexpected complexity.

Both the creation of initial content as well as the updates per push
create commits that match the history of the original commits. This way,
the generated diffs match the original diffs best. To do so, we need to
create a DAG that only has the commits we're interested in. Details on the
creation of the graph for a subset of commits are described in :doc:`graph`.
