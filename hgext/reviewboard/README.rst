================================
Review Board Mercurial Extension
================================

This extension allows Mercurial to publish Review Board reviews by
pushing to a repository.

This extension consists of both a client and server component. The
two pieces communicate with each other over the Mercurial wire
protocol during push operations. The client passes necessary
review information to the server and the server talks to a
Review Board API to create the review.

Wire Protocol
=============

The server implements a new command, ``reviewboard``. The command
input and output is a newline-delimited message.

The first line of the message is an integer version number of the
protocol version.

Request Version 1
-----------------

The lines of the request message are as follows:

* Bugzilla username (%XX encoded)
* Bugzilla password (%XX encoded)
* Space delimited list of hex nodes that should be reviewed
* Review identifier (%XX encoded)

The server will create a review of the changesets specified using
review identifier specified to track the review.

Response Version 1
------------------

The lines of the response are prefixed with a line type. The following
prefixes are supported:

``display:``
   These lines should be displayed on the client.
``reviewid:``
   The identifier of the main Review Board review for this push.
