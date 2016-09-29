  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting wip doesn't install it

  $ hg --config ui.interactive=true --config configwizard.steps=wip,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  It is common to want a quick view of changesets that are in progress.
  
  The ``hg wip`` command provides such a view.
  
  Example Usage:
  
    $ hg wip
    o   4084:fcfa34d0387b dminor @
    |  mozreview: use repository name when displaying treeherder results (bug 1230548) r=mcote
    | @   4083:786baf6d476a gps
    | |  mozreview: create child review requests from batch API
    | o   4082:3f100fa4a94f gps
    | |  mozreview: copy more read-only processing code; r?smacleod
    | o   4081:939417680cbe gps
    |/   mozreview: add web API to submit an entire series of commits (bug 1229468); r?smacleod
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg wip` alias (Yn)?  n

wip enabled when requested

  $ hg --config configwizard.steps=wip,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  It is common to want a quick view of changesets that are in progress.
  
  The ``hg wip`` command provides such a view.
  
  Example Usage:
  
    $ hg wip
    o   4084:fcfa34d0387b dminor @
    |  mozreview: use repository name when displaying treeherder results (bug 1230548) r=mcote
    | @   4083:786baf6d476a gps
    | |  mozreview: create child review requests from batch API
    | o   4082:3f100fa4a94f gps
    | |  mozreview: copy more read-only processing code; r?smacleod
    | o   4081:939417680cbe gps
    |/   mozreview: add web API to submit an entire series of commits (bug 1229468); r?smacleod
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg wip` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,6 @@
  +[alias]
  +wip = log --graph --rev=wip --template=wip
  +[revsetalias]
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed()
  +[templates]
  +wip = '{label("log.branch", branches)} {label("changeset.{phase}", rev)}{label("changeset.{phase}", ":")}{label("changeset.{phase}", short(node))} {label("grep.user", author|user)}{label("log.tag", if(tags," {tags}"))}{label("log.tag", if(fxheads," {fxheads}"))} {label("log.bookmark", if(bookmarks," {bookmarks}"))}\n{label(ifcontains(rev, revset("."), "desc.here"),desc|firstline)}'
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [alias]
  wip = log --graph --rev=wip --template=wip
  [revsetalias]
  wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed()
  [templates]
  wip = '{label("log.branch", branches)} {label("changeset.{phase}", rev)}{label("changeset.{phase}", ":")}{label("changeset.{phase}", short(node))} {label("grep.user", author|user)}{label("log.tag", if(tags," {tags}"))}{label("log.tag", if(fxheads," {fxheads}"))} {label("log.bookmark", if(bookmarks," {bookmarks}"))}\n{label(ifcontains(rev, revset("."), "desc.here"),desc|firstline)}'

wip alias has pager configuration when pager enabled

  $ hg --config configwizard.steps=pager,wip,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  1
  It is common to want a quick view of changesets that are in progress.
  
  The ``hg wip`` command provides such a view.
  
  Example Usage:
  
    $ hg wip
    o   4084:fcfa34d0387b dminor @
    |  mozreview: use repository name when displaying treeherder results (bug 1230548) r=mcote
    | @   4083:786baf6d476a gps
    | |  mozreview: create child review requests from batch API
    | o   4082:3f100fa4a94f gps
    | |  mozreview: copy more read-only processing code; r?smacleod
    | o   4081:939417680cbe gps
    |/   mozreview: add web API to submit an entire series of commits (bug 1229468); r?smacleod
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg wip` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -4,3 +4,12 @@
   wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed()
   [templates]
   wip = '{label("log.branch", branches)} {label("changeset.{phase}", rev)}{label("changeset.{phase}", ":")}{label("changeset.{phase}", short(node))} {label("grep.user", author|user)}{label("log.tag", if(tags," {tags}"))}{label("log.tag", if(fxheads," {fxheads}"))} {label("log.bookmark", if(bookmarks," {bookmarks}"))}\n{label(ifcontains(rev, revset("."), "desc.here"),desc|firstline)}'
  +[extensions]
  +pager =
  +[pager]
  +pager = LESS=FRSXQ less
  +attend-help = true
  +attend-incoming = true
  +attend-outgoing = true
  +attend-status = true
  +attend-wip = true
  
  Write changes to hgrc file (Yn)?  y

wip alias ignores old esrs if using firefoxtree

  $ hg --config configwizard.steps=firefoxtree,wip,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The firefoxtree extension makes interacting with the multiple Firefox
  repositories easier:
  
  * Aliases for common trees are pre-defined. e.g. `hg pull central`
  * Pulling from known Firefox trees will create "remote refs" appearing as
    tags. e.g. pulling from fx-team will produce a "fx-team" tag.
  * The `hg fxheads` command will list the heads of all pulled Firefox repos
    for easy reference.
  * `hg push` will limit itself to pushing a single head when pushing to
    Firefox repos.
  * A pre-push hook will prevent you from pushing multiple heads to known
    Firefox repos. This acts quicker than a server-side hook.
  
  The firefoxtree extension is *strongly* recommended if you:
  
  a) aggregate multiple Firefox repositories into a single local repo
  b) perform head/bookmark-based development (as opposed to mq)
  
  (Relevant config option: extensions.firefoxtree)
  
  Would you like to activate firefoxtree (Yn)?  y
  It is common to want a quick view of changesets that are in progress.
  
  The ``hg wip`` command provides such a view.
  
  Example Usage:
  
    $ hg wip
    o   4084:fcfa34d0387b dminor @
    |  mozreview: use repository name when displaying treeherder results (bug 1230548) r=mcote
    | @   4083:786baf6d476a gps
    | |  mozreview: create child review requests from batch API
    | o   4082:3f100fa4a94f gps
    | |  mozreview: copy more read-only processing code; r?smacleod
    | o   4081:939417680cbe gps
    |/   mozreview: add web API to submit an entire series of commits (bug 1229468); r?smacleod
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg wip` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,11 +1,12 @@
   [alias]
   wip = log --graph --rev=wip --template=wip
   [revsetalias]
  -wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed()
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed() and not (fxheads() - date(-90))
   [templates]
   wip = '{label("log.branch", branches)} {label("changeset.{phase}", rev)}{label("changeset.{phase}", ":")}{label("changeset.{phase}", short(node))} {label("grep.user", author|user)}{label("log.tag", if(tags," {tags}"))}{label("log.tag", if(fxheads," {fxheads}"))} {label("log.bookmark", if(bookmarks," {bookmarks}"))}\n{label(ifcontains(rev, revset("."), "desc.here"),desc|firstline)}'
   [extensions]
   pager =
  +firefoxtree = */hgext/firefoxtree (glob)
   [pager]
   pager = LESS=FRSXQ less
   attend-help = true
  
  Write changes to hgrc file (Yn)?  y
