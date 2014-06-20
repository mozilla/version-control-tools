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
