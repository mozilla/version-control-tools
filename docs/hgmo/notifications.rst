.. _hgmo_notification:

====================
Change Notifications
====================

hg.mozilla.org publishes notifications when various events occur, such as
a push to a repository.

Common Properties of Notifications
==================================

Notifications are sent after an event has been completely replicated to all
active HTTPS replication mirrors.

.. note::

   Unlike polling the pushlog, reacting to data advertised by these
   notifications is not susceptible to race conditions when one mirror
   may have replicated data before another.

hg.mozilla.org guarantees chronological writing of notifications within
individual repositories only. Assume we have 2 repositories, ``X`` and ``Y``
with pushes occurring in the order of ``X1``, ``Y1``, ``X2``, ``Y2``. We only
guarantee that ``X1`` is delivered before ``X2`` and ``Y1`` is delivered before
``Y2``. In other words, it is possible for ``Y1`` (or even ``Y2``) to be
delivered before ``X1`` (or ``X2``).

Delivered messages have a *type*. The sections that follow describe the
format/schema of each message type.

``changegroup.1``
-----------------

This message type describes a push that introduced changesets (commits) on
a repository.

The fields of this message type constitute the root fields of messages
publishes to the ``exchange/hgpushes/v1`` exchange.

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

   The list should only be empty for special repositories, such as the
   experimental unified repositories.

   The composition of this dict is described below.
``source``
   Where this changeset came from.

   The value will almost always be ``push``.

   *(Not present in ``exchange/hgpushes/v1`` messages)*

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

``newrepo.1``
-------------

This message is sent when a new repository is created.

This message has the following fields:

``repo_url``
   URL of the created repository.

``obsolete.1``
--------------

This message describes obsolescence markers added on a repository.

Obsolescence markers tell when a changeset was *obsoleted* and should
no longer be exposed to the outside world, effectively hiding it from
history.

Essentially, an obsolescence marker contains a *precursor* node and a
list of 0 or more *successor* nodes. The *precursor* node is hidden as
a result of the creation of a marker. The *successor* nodes are the nodes
that replaced the *precursor* node. If there is no replacement (the
changeset was dropped), the list of *successors* is empty.

This message has the following fields:

markers
   A list of dicts describing each obsolescence marker in detail. The
   format of these entries is described below.
repo_url
   The URL of the repository this marker applies to.

Each ``markers`` entry is a dict with the following fields:

precursor
   Dict describing the *precursor* node.
successors
   List of dicts describing the *successor* nodes.
user
   String user that produced this marker (this comes from Mercurial's
   ``ui.username`` config option).
time
   Float corresponding to number of seconds since UNIX epoch time when
   this marker was produced.

The fields of a ``precursor`` or ``successors`` dict are as follows:

node
   40 character SHA-1 of changeset.
known
   Bool indicating whether the changeset is known to the repo. Sometimes
   obsolescence markers reference changesets not pushed to the repo. This
   flag helps consumers know whether they might be able to query the repo
   for more info about this changeset.
visible
   Bool indicating whether the changeset is visible to the repository at the
   time the message was created. If ``false``, the changeset is known but
   hidden. Value is ``null`` if the changeset is known ``known``.

   Even if the value is ``true``, there is no guarantee a consumer of this
   message will be able to access changeset metadata from the repository,
   as a subsequent obsolescence marker could have made this changeset
   hidden by the time the consumer sees this message and queries the
   repository. This is one reason why this data structure contains changeset
   metadata that would normally be obtained by the consumer.
desc
   String of commit message for the changeset. May be null if the changeset
   is not known to the repo.
push
   Dict describing the pushlog entry for this changeset.

   Will be ``null`` if the changeset is not known or if there isn't a pushlog
   entry for it.

   The content of this dict matches the entries from ``pushlog_pushes``
   from ``changeset.1`` messages.

Examples
--------

An example message payload for is as follows::

   {
     "type": "changegroup.1",
     "data": {
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
   }

Pulse Notifications
===================

hg.mozilla.org guarantees at least once delivery of
`Pulse <https://wiki.mozilla.org/Auto-tools/Projects/Pulse>`_ messages when a
push is performed to the server.

Pulse messages are written to the following exchanges:

* `exchange/hgpushes/v1 <https://tools.taskcluster.net/pulse-inspector/#!((exchange:exchange/hgpushes/v1,routingKeyPattern:%23))>`_
* (experimental) `exchange/hgpushes/v2 <https://tools.taskcluster.net/pulse-inspector/#!((exchange:exchange/hgpushes/v2,routingKeyPattern:%23))>`_

The routing key for each message is the relative path of the repository
on hg.mozilla.org (e.g. ``mozilla-central`` or ``integration/mozilla-inbound``).

The ``payload`` of the JSON messages published to Pulse depend on the exchange.

The ``exchange/hgpushes/v1`` exchange only supported publishing *push events*
that described a push. The ``exchange/hgpushes/v2`` exchange supports publishing
multiple event types.

.. important::

   New message types can be added to the ``exchange/hgpushes/v2`` exchange at
   any time.

   Consumers should either ignore unknown message types or fail fast when
   encountering one.

The ``exchange/hgpushes/v2`` exchange has a payload with the following keys:

``type``
   String denoting the message type.
``data``
   Dictionary holding details about the event.

The message types and their data are described later in this document.

SNS Notifications
=================

Change events for hg.mozilla.org are published to
`Amazon Simple Notification Service (SNS) <https://aws.amazon.com/sns/>`_.

Messages are published to SNS topic
``arn:aws:sns:us-west-2:699292812394:hgmo-events``.

The message is JSON with the following keys:

``type``
   String denoting the message type.
``data_url``
   URL where JSON describing the event can be obtained.
``data`` (optional)
   Dictionary holding details about the event.
``external`` (optional)
   Boolean indicating whether data is only available externally.
   If this key is present, ``data`` will not be present and the only
   way to obtain data is to query ``data_url``.
``repo_url`` (optional)
   URL of repository from which this data originated. This key is only
   present if ``data`` is not present, as this value is already recorded
   inside ``data``. The main purpose of this key is to facilitate
   message filtering without having to query ``data_url`` to determine
   which repository the message belongs to.

The message types and their data are described later in this document.

At least once delivery is guaranteed. And, new message types may be
introduced at any time.
