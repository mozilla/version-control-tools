rbbz: Review Board extension for Bugzilla support
=================================================

rbbz is a [Review Board extension][] that integrates a Bugzilla user
database.  It adds an authentication back end, which, when enabled,
authenticates against Bugzilla's XMLRPC API instead of the local
Review Board database.  When active, Review Board's User List web API,
used by the UI's autosuggest, also queries Bugzilla.


Installation
------------

As described in Review Board's [extension installation docs][],
install rbbz like any other Python package, e.g.

    pip install rbbz

In the Review Board admin UI, go to the Extensions page and enable
rbbz.  You'll then have to go to the Authentication settings and
change the Authentication Method to "Bugzilla".  A setting for
"Bugzilla XMLRPC URL" will appear.  Enter the URL to your Bugzilla
installation's XMLPRC API, e.g. https://bugzilla.yourdomain/xmlrpc.cgi.

At this point you should be able to log out and log back in with your
Bugzilla credentials.  Similarly, when you choose people for a review,
the autosuggest should return results from the Bugzilla user database.


Technical Notes
---------------

In order to stay generic, Review Board's User List web API always
searches the local database.  To provide support for Bugzilla, rbbz
overrides a function called early in the User List function in order
to send a user-search query to Bugzilla.  It then writes the results
to the Review Board user table, updating existing entries and creating
new ones when needed.


To Do
-----

* Support for Bugzilla's REST API (as an option, so older Bugzilla
  systems are still supported).

* Caching in User List to avoid always searching the Bugzilla
  database, if possible.

[Review Board extension]: http://www.reviewboard.org/docs/manual/dev/extending/
[extension installation docs]: http://www.reviewboard.org/docs/manual/dev/admin/extensions/#installing-extensions
