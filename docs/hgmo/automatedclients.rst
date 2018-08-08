.. _hgmo_automatedclients:

=================
Automated Clients
=================

Do you have or want to run an automated consumer of hg.mozilla.org?
Then this document is for you.

Read on to learn about the should and should nots of automatically
consuming the hg.mozilla.org service.

When reading sections that recommend *not* doing something, keep in
mind that https://hg.mozilla.org/ is ultimately a service in support
of various Mozilla projects. The recommendation to *not* do something
is not a hard or fast *no*: it is more of a preference so we can
avoid operational issues. If you find yourself having to perform
a lot of work to abide by the guidelines in this document, you should
approach the hg.mozilla.org service operators to discuss alternatives
to make your job easier. The
`hgmo-service-discuss@mozilla.com <mailto:hgmo-service-discuss@mozilla.com>`_
mailing list (contents are private) is a good way to get in touch.

Identifying Clients
===================

Automated requests to https://hg.mozilla.org/ that belong to
a well-defined service should use a custom `User-Agent` HTTP
request header to identify themselves. This is so server operators
can better assess the impact that individual clients have on
the server.

.. important::

   Server operators reserve the right to block generic `User-Agent`
   values that are contributing abnormally high load. Using a custom
   `User-Agent` lessens the possibility of being blocked due to
   `User-Agent` name conflict with a malicious agent also not using
   a custom `User-Agent`.

Limiting Concurrent Requests
============================

https://hg.mozilla.org/ does not have infinite capacity and clients
issuing several concurrent HTTP requests can cause capacity
problems on the server.

In general, any single logical client should not attempt to issue
more than 10 concurrent HTTP requests. This limit applies whether
the requests are issued from a single IP or across several IPs.

The fewer concurrent requests that are issued, the lesser the
load impact on the server. However, this obviously increases the
time for the client to finish all the requests. So it's a trade-off.

Limiting Request Volume
=======================

Again, https://hg.mozilla.org/ does not have infinite capacity. Clients
issuing thousands of HTTP requests can contribute significant server
load, especially to certain endpoints.

Clients should be respectful of server capacity limitations and try
to limit the total number of requests. This especially holds true
for requests that take more than 1.0s to complete or transfer a
lot of data from server to client.

Repository data on https://hg.mozilla.org/ (including pushlog and
other custom data) can often be cloned to a local machine. Such is the
nature of distributed version control. Once on the local machine, one
can use `hg serve` to run a local HTTP server which exposes much of
the same data as https://hg.mozilla.org/. Or one can use `hg` commands
to access repository data.

Clients needing to query large parts of the repository (e.g. to collect
information on every changeset or file) are highly encouraged to query
data offline, if possible.

Obtaining Recent Changes
========================

It is common for clients to want to know when a change occurs on
hg.mozilla.org so that they can do something in reaction to it.

There are two mechanisms for determining when changes occur:
:ref:`subscription-based notifications <hgmo_notifications>` and
polling HTTP-based APIs on hg.mozilla.org.

For the push-based notifications, clients can subscribe to e.g.
SNS or Pulse queues and receive messages milliseconds after they
are published by hg.mozilla.org.

For polling, typically the :ref:`pushlog <pushlog>` HTTP+JSON API
is used. Clients need to periodically query the pushlog and see
if anything has changed since the last query.

The recommend mechanism for learning about recent changes is to
subscribe to one of the push-based notifications (e.g. SNS or Pulse).
This allows clients to see changes to *any* repository milliseconds
after it occurs.

While it shouldn't occur frequently, subscription-based mechanisms
can be lossy. e.g. if the subscriber is detached - possibly for a
long-enough time - it may lose an event. For that reason, robust
consumers without a tolerance for data loss should supplement
subscription-based monitoring with pushlog polling. If subscriptions
*lose* an event, the polling fallback should catch any events that
fell through. Because subscriptions shouldn't be lossy, the pushlog
polling interval can be relatively high - say every 5 minutes.

If clients want to react to an event in an expedient manner (say under
a minute), they should use subscription-based notifications.

If latency is not important, it is acceptable to use polling.

.. important::

   Clients should not poll repository endpoints on
   https://hg.mozilla.org/ more frequently than once every minute,
   as this can contribute significant load to the servers.

   If clients really need to react to events with that little latency,
   they should be using subscription-based notification mechanisms.
