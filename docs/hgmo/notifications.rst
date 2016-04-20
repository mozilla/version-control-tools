.. _hgmo_notification:

====================
Change Notifications
====================

Pulse Notifications
===================

hg.mozilla.org guarantees at least once delivery of
`Pulse <https://wiki.mozilla.org/Auto-tools/Projects/Pulse>`_ messages when a
push is performed to the server.

Pulse messages are written to the
`exchange/hgpushes/v1 <https://tools.taskcluster.net/pulse-inspector/#!((exchange:exchange/hgpushes/v1,routingKeyPattern:%23>`_
exchange under the ``hg.push.1`` routing key.

Pulse messages are written after the push has been completely replicated to
all active HTTPS replication mirrors.

.. note::

   Unlike polling the pushlog, reacting to data advertised by Pulse events
   is not susceptible to race conditions when one mirror may have replicated
   data before another.

hg.mozilla.org guarantees chronological writing of Pulse messages within
individual repositories only. Assume we have 2 repositories, ``X`` and ``Y``
with pushes occurring in the order of ``X1``, ``Y1``, ``X2``, ``Y2``. We only
guarantee that ``X1`` is delivered before ``X2`` and ``Y1`` is delivered before
``Y2``. In other words, it is possible for ``Y1`` (or even ``Y2``) to be
delivered before ``X1`` (or ``X2``).

The ``payload`` of the JSON messages published to Pulse contain the following
keys:

``repo_url``
   The URL of the repository that was pushed to.
``heads``
   A list of 40 character SHA-1 changesets that are DAG heads resulting
   from this push. Typically, there is only 1 entry (because most pushes
   only push 1 head).
``pushlog_pushes``
   A list of dicts describing each :ref:`pushlog` entry related to
   changesets in this push. This list *should* be a single item. But
   it can be empty. If you see multiple entries, please say something
   in ``#vcs``.

   The composition of this dict is described below.

Each ``pushlog_pushes`` entry consists of the following keys:

``pushid``
   Integer pushlog ID.
``time``
   Integer UNIX timestamp the push occurred, as recorded by the pushlog.
``user``
   The authenticated user that performed the push. Typically an e-mail
   address.
``push_json_url``
   URL of JSON endpoint that describes this push in more detail.
``push_full_json_url``
   URL of JSON endpoint that describes this push in even more detail
   (lists files that changed, etc). See :ref:`pushlog` for what the
   ``json-pushes`` JSON API returns.

An example Pulse message payload is as follows::

   {
     "repo_url": "https://hg.mozilla.org/try",
     "heads": ["eb6d9371407416e488d2b2783a5a79f8364330c8"],
     "pushlog_pushes": {
       "time": 14609750810,
       "pushid": 120040,
       "user": "tlin@mozilla.com",
       "push_json_url": "https://hg.mozilla.org/try/json-pushes?version=2&startID=120039&endID=120040",
       "push_full_json_url": "https://hg.mozilla.org/try/json-pushes?version=2&full=1&startID=120039&endID=120040"
     }
   }
