.. _pushlog:

=======
Pushlog
=======

Mozilla has taught Mercurial how to record who pushes what where and
when. This is called the *pushlog*. It is essentially a log of pushes to
repositories.

Technical Details
=================

All pushes to ``hg.mozilla.org`` occur via SSH. When clients talk to
the server, the authenticated username from SSH is stored in the
``USER`` environment variable. When a push occurs, our custom
``pushlog`` Mercurial extension will record the username, the current
time, and the list of changesets that were pushed in a SQLite database
in the repository.

Installing
==========

The *pushlog* extension (source in ``hgext/pushlog``) contains the core
data recording and data replication code. When installed, a
``pretxnchangegroup`` hook inserts pushlog entries when changesets are
introduced. To install this extension, add the following line to your
hgrc::

   [extensions]
   pushlog = /path/to/version-control-tools/hgext/pushlog

No additional configuration is necessary.

The web components for pushlog are separate from the core extension and
require a bit more effort to configure. This code lives in
``hgext/pushlog-legacy``. It is our intention to eventually aggregate
this code into ``hgext/pushlog`` so there is a unified pushlog
experience.

The web component will require the following extension::

   [extensions]
   pushlog-feed = /path/to/version-control-tools/hgext/pushlog-legacy/pushlog-feed.py

``pushlog-feed.py`` exposes some hgweb endpoints that expose pushlog
data.

Templates
---------

It isn't enough to activate the ``pushlog-feed`` extension: you'll also
need to configure some
`Mercurial theming <http://mercurial.selenic.com/wiki/Theming>`_
to render pushlog data.

The Atom output will require the existence of an ``atom`` style. You are
encouraged to copy the files in ``hgtemplates/atom`` to your Mercurial
styles directory.

The ``pushloghtml`` page will render the ``pushlog`` template. This is
something you'll need to define. Look for ``pushlog.tmpl`` files in
``hgtemplates/`` in this repository for examples.

Pushlog templates typically make use of a named ``pushlogentry``
entity. You may also need to define this. Searching for ``pushlog`` in
``hgtemplates`` to find all references is probably a good idea.

Pushlog Wire Protocol Command
=============================

The ``pushlog`` extension exposes a ``pushlog`` command and capability
to the Mercurial wire protocol. This enables Mercurial clients to
retrieve pushlog data directly from the wire protocol.

For more details, read the source in ``hgext/pushlog/__init__.py``.

The Push ID
===========

Entries in the pushlog have an incrementing integer key that uniquely
identifies them. It is guaranteed that push ID ``N + 1`` occurs after
``N``.

hgweb Commands
==============

There are a couple custom hgweb commands that expose pushlog
information.

For reference, an *hgweb command* is essentially a per-repository
handler in hgweb (Mercurial's HTTP interface). URLs have the form
``https://hg.mozilla.org/<repository>/<command>/<args>``.

json-pushes Command
-------------------

The ``json-pushes`` command exposes JSON representation of pushlog data.

pushlog Command
---------------

The ``pushlog`` command exposes an ATOM feed of pushes to the
repository.

It behaves similarly to ``json-pushes`` in terms of what
parameters it can accept.

pushloghtml Command
-------------------

The ``pushloghtml`` command exposes HTML show pushlog data.

Query Parameters
----------------

Various hgweb pushlog commands accept query string parameters to control
what data is returned.

The following parameters control selection of the lower bound of pushes.
Only 1 takes effect at a time. The behavior of specifying multiple
parameters is undefined.

startdate
   A string defining the start date to query pushes from. Only pushes
   after this date (non-inclusive) will be returned.

fromchange
   Only return pushes that occurred after the push that introduced this
   changeset. The value can be any changeset identifier that Mercurial
   can resolve. This is typically a 40 byte changeset SHA-1.

startID
   Only return pushes whose ID is greater than the integer specified.

The following parameters control selection of the upper bound of pushes.
Behavior is similar to the parameters that control the lower bound.

enddate
   A string defining the end date for pushes. Only pushes before this
   date (non-inclusive) will be returned.

tochange
   Only return pushes up to and including the push that introduced the
   specified changeset.

endID
   Only return pushes up to and including the push with the specified
   push ID.

Only parameters that control behavior include:

user
   Only show pushes performed by the specified user.

changeset
   Only show pushes that introduced the specified changeset.

tipsonly
   If the value is ``1``, only return info from the tip-most changeset
   in the push.  The default is to return info for all changesets in a
   push.

full
   If this parameter is present (the value is ignored), responses will
   contain more verbose info for each changeset.

version
   Format of the response. ``1`` and ``2`` are accepted. ``1`` is the
   default (for backwards compatibility).

   This is only used by ``json-pushes``.

Dates can be specified a number of ways. However, using seconds since
UNIX epoch is highly preferred.

JSON Payload Formats
--------------------

Version 1
^^^^^^^^^

Version 1 (the default) consists of a JSON object with keys
corresponding to push IDs and values containing metadata about just the
push. e.g.::

   {
     "16": {
       "changesets": [
       "91826025c77c6a8e5711735adaa9766dd4eac7fc",
       "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
      ],
      "date": 1227196396,
      "user": "gszorc@mozilla.com"
     }
   }

Version 2
^^^^^^^^^

Version 2 introduces a container for pushes so that additional metadata
can be communicated in the main object in the payload. Here is an
example payload::

   {
     "lastpushid": 21,
     "pushes": {
       "16": {
         "changesets": [
           "91826025c77c6a8e5711735adaa9766dd4eac7fc",
           "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
         ],
         "date": 1227196396,
         "user": "gszorc@mozilla.com"
       }
     }
   }

The top-level objects contains the following properties:

pushes
   An object containing push information.

   This is the same object that constitutes version 1's response.

lastpushid
   The push ID of the most recent push known to the database.

   This value can be used by clients to determine if more pushes are
   available. For example, clients may query for N changesets at a time
   by specifying ``endID``. The value in this property can tell these
   clients when they have exhausted all known pushes.

Push Objects
^^^^^^^^^^^^

The value of each entry in the pushes object is an object describing
the push and the changesets therein.

The following properties are always present:

changesets
   An array of 40 character changeset SHA-1s that were included in the
   push. Changesets are included in DAG/revlog order. The tip-most
   changeset is last.

date
   Integer seconds since UNIX epoch that the push occurred.

   For pushes that take a very long time (more than a single second),
   the data will be recorded towards the end of the push, just before
   the transaction is committed to Mercurial. Although, this is an
   implementation details.

   There is no guarantee of strict ordering between dates. i.e. the
   ``date`` of push ID ``N + 1`` could be less than the ``date`` of push
   ID ``N``. Such is how clocks work.

user
   The string username that performed the push.

If ``full`` is specified, each entry in the ``changesets`` array will be
an object instead of a string. Each object will have the following
properties:

node
   The 40 byte hex SHA-1 of the changeset.

author
   The author string from the changeset.

desc
   The changeset's commit message.

branch
   The branch the changeset belongs to.

   ``default`` is the default branch in Mercurial.

tags
   An array of string tags belonging to this changeset.

files
   An array of filenames that were changed by this changeset.

Here's an example::

   {
     "author": "Eugen Sawin <esawin@mozilla.com>",
     "branch": "default",
     "desc": "Bug 1110212 - Strong randomness for Android DNS resolver. r=sworkman",
     "files": [
      "other-licenses/android/res_init.c"
     ],
     "node": "ee4fe2ec168e719e822dabcdd797c0cff9ce2407",
     "tags": []
   }

Writing Agents that Consume Pushlog Data
========================================

It is common to want to write tools or services that consume pushlog
data. For example, you may wish to perform processing of new commits as
they arrive.

In the ideal world, we would expose a notification service to enable
near real-time consumption of this data. Until that service is built,
clients will have to resort to polling the pushlog. Furthermore, the
pushlog only exposes data for 1 repository at a time. If you are
interested in consuming data for multiple repositories, you'll need
to query each repository/pushlog separately.

When implementing agents that consume pushlog data, please keep in mind
the following best practices:

1. Query by push ID, not by changeset or date.
2. Always specify a ``startID`` and ``endID``.
3. Try to avoid ``full`` if possible.
4. Always use the latest format version.
5. Don't be afraid to ask for a new pushlog feature to make your life
   easier.

Querying by push ID is preferred because date ordering is not guaranteed
(due to system clock skew) and because changesets can occur in multiple
pushes in :ref:`headless_repositories`. If a changeset occurs in
multiple pushes, using the changeset as an identifier is ambiguous! Push
IDs are the only guaranteed stable method for selecting pushes.

We recommend that ``startID`` and ``endID`` always be specified so
response sizes are bound. If they are omitted, the server may generate a
very large payload. We've seen clients request **all** push data from
the server and the response JSON is over 100 MB!

Specifying ``full`` will incur an additional lookup on the server.
Without ``full``, the response JSON is generated purely from the SQLite
database. With ``full``, data needs to be read from Mercurial. This adds
overhead to the lookup and to the transfer. If you don't need the extra
data, please don't request it.
