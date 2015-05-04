.. _hgmozilla_issues:

===============================
Reporting Issues with Mercurial
===============================

Are you having a bad experience with Mercurial or with hg.mozilla.org?
Read on to learn how to report it and (hopefully) get it resolved.

Mercurial and Mozilla
=====================

The Mercurial project cares about Mozilla because the Firefox repository
is one of the largest open source Mercurial repositories both in terms
of repository size and number of users. Because of that scale, Mozillians
tend to notice issues with Mercurial before others. As such, the Mercurial
project is very keen to learn about and address the problems Mozillians may
have.

How to Report Issues
====================

With hg.mozilla.org
-------------------

Notice something weird on hg.mozilla.org (including performance problems)?
Please file a bug against
[Developer Services :: hg.mozilla.org](https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org).

If you want to talk with someone before filing a bug, hop in to #vcs on
irc.mozilla.org. That is a low traffic channel and your question should be
answered eventually.

With Core Mercurial
-------------------

Found a bug in Mercurial? Have a performance concern? File a bug in
[Mercurial's Bugzilla](http://bz.selenic.com/). Choose the *Mercurial*
component if you are unsure what component to use.

Before filing bugs, ensure you are using the latest Mercurial release. If not,
the first thing people will ask you is to try to reproduce with the latest
release.

When filing bugs, practice good bug filing etiquite and try to include steps
to reproduce.

.. tip::

   Many Mercurial developers have a copy of mozilla-central for performance
   testing. Bug reports that reference mozilla-central (or any public
   repository for that matter) are acceptable.

If you are unsure whether something is a bug, hop in to #mercurial on the
Freenode IRC network and ask around. Or, post to one of the Mercurial
[mailing lists](http://mercurial.selenic.com/wiki/MailingLists).

With a Mozilla Extensions
-------------------------

Mozillians have authored a handful of Mercurial extensions. If you find a
bug in one, file a bug against that extension's Bugzilla component.
These components all exist in the *Developer Services* product on
bugzilla.mozilla.org.

Before filing bugs, ensure you are using the latest Mercurial release and
that your version-control-tools repo (the repo containing most of the
extensions) is fully up to date. Otherwise, you may be reporting a bug that's
been fixed already.

How Not to Report Issues
========================

Please do not complain about issues (e.g. on #developers) without telling
someone who can do something about it. Otherwise, you have effectively
complained to a black hole and your problems will likely persist because
someone empowered to do something about them doesn't know of them.

If you see something, file something! Don't be just a complainer: be an
enabler.

