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
  
  ``hg show`` can describe active bookmarks, the current stack, or a
  tree of changesets that are in development.
  ``hg wip`` provides a Mozilla-specific overview of in-progress changesets: 
  
  Example Usage:
  
    $ hg wip
    @  5887 armenzg tip @ Bug 1313661 - Bump pushlog_client to 0.6.0. r=me
    : o  5885 glob mozreview: Improve the error message when pushing to a submitted/discarded review request (bug 1240725) r?smacleod
    : o  5884 glob hgext: Support line breaks in hgrb error messages (bug 1240725) r?gps
    :/
    o  5883 mars mozreview: add py.test and demonstration tests to mozreview (bug 1312875) r=smacleod
    : o  5881 glob autoland: log mercurial commands to autoland.log (bug 1313300) r?smacleod
    :/
    o  5250 gps ansible/docker-hg-web: set USER variable in httpd process
    |
    ~
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: extensions.show, alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg show` extension and `hg wip` alias (Yn)?  n

wip enabled when requested

  $ hg --config configwizard.steps=wip,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  It is common to want a quick view of changesets that are in progress.
  
  ``hg show`` can describe active bookmarks, the current stack, or a
  tree of changesets that are in development.
  ``hg wip`` provides a Mozilla-specific overview of in-progress changesets: 
  
  Example Usage:
  
    $ hg wip
    @  5887 armenzg tip @ Bug 1313661 - Bump pushlog_client to 0.6.0. r=me
    : o  5885 glob mozreview: Improve the error message when pushing to a submitted/discarded review request (bug 1240725) r?smacleod
    : o  5884 glob hgext: Support line breaks in hgrb error messages (bug 1240725) r?gps
    :/
    o  5883 mars mozreview: add py.test and demonstration tests to mozreview (bug 1312875) r=smacleod
    : o  5881 glob autoland: log mercurial commands to autoland.log (bug 1313300) r?smacleod
    :/
    o  5250 gps ansible/docker-hg-web: set USER variable in httpd process
    |
    ~
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: extensions.show, alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg show` extension and `hg wip` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,19 @@
  +[alias]
  +wip = log --graph --rev=wip --template=wip
  +[extensions]
  +show =
  +[revsetalias]
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed() (no-hg46 !)
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or orphan()^) and not closed() (hg46 !)
  +[templates]
  +wip = '{label("wip.branch", if(branches,"{branches} "))}{label(ifeq(graphnode,"x","wip.obsolete","wip.{phase}"),"{rev}:{node|short}")}{label("wip.user", " {author|user}")}{label("wip.tags", if(tags," {tags}"))}{label("wip.tags", if(fxheads," {fxheads}"))}{if(bookmarks," ")}{label("wip.bookmarks", if(bookmarks,bookmarks))}{label(ifcontains(rev, revset("parents()"), "wip.here"), " {desc|firstline}")}'
  +[color]
  +wip.bookmarks = yellow underline
  +wip.branch = yellow
  +wip.draft = green
  +wip.here = red
  +wip.obsolete = none
  +wip.public = blue
  +wip.tags = yellow
  +wip.user = magenta
  +[experimental]
  +graphshorten = true
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [alias]
  wip = log --graph --rev=wip --template=wip
  [extensions]
  show = 
  [revsetalias]
  wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed() (no-hg46 !)
  wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or orphan()^) and not closed() (hg46 !)
  [templates]
  wip = '{label("wip.branch", if(branches,"{branches} "))}{label(ifeq(graphnode,"x","wip.obsolete","wip.{phase}"),"{rev}:{node|short}")}{label("wip.user", " {author|user}")}{label("wip.tags", if(tags," {tags}"))}{label("wip.tags", if(fxheads," {fxheads}"))}{if(bookmarks," ")}{label("wip.bookmarks", if(bookmarks,bookmarks))}{label(ifcontains(rev, revset("parents()"), "wip.here"), " {desc|firstline}")}'
  [color]
  wip.bookmarks = yellow underline
  wip.branch = yellow
  wip.draft = green
  wip.here = red
  wip.obsolete = none
  wip.public = blue
  wip.tags = yellow
  wip.user = magenta
  [experimental]
  graphshorten = true

Ensure `hg wip` actually works. We do this before the version-mock tests
to ensure the alias works on the hg version being tested

  $ hg init repo
  $ cd repo
  $ touch foo
  $ echo "test123" >> foo
  $ hg add foo
  $ hg -q commit -m "test commit"
  $ HGRCPATH=$TESTTMP/.hgrc hg debugrevspec wip
  0
  $ cd ..


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
  b) perform head/bookmark-based development
  
  (Relevant config option: extensions.firefoxtree)
  
  Would you like to activate firefoxtree (Yn)?  y
  It is common to want a quick view of changesets that are in progress.
  
  ``hg show`` can describe active bookmarks, the current stack, or a
  tree of changesets that are in development.
  ``hg wip`` provides a Mozilla-specific overview of in-progress changesets: 
  
  Example Usage:
  
    $ hg wip
    @  5887 armenzg tip @ Bug 1313661 - Bump pushlog_client to 0.6.0. r=me
    : o  5885 glob mozreview: Improve the error message when pushing to a submitted/discarded review request (bug 1240725) r?smacleod
    : o  5884 glob hgext: Support line breaks in hgrb error messages (bug 1240725) r?gps
    :/
    o  5883 mars mozreview: add py.test and demonstration tests to mozreview (bug 1312875) r=smacleod
    : o  5881 glob autoland: log mercurial commands to autoland.log (bug 1313300) r?smacleod
    :/
    o  5250 gps ansible/docker-hg-web: set USER variable in httpd process
    |
    ~
  
  (Not shown are the colors that help denote the state each changeset
  is in.)
  
  (Relevant config options: extensions.show, alias.wip, revsetalias.wip, templates.wip)
  
  Would you like to install the `hg show` extension and `hg wip` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -2,8 +2,9 @@
   wip = log --graph --rev=wip --template=wip
   [extensions]
   show =
  +firefoxtree = */hgext/firefoxtree (glob)
   [revsetalias]
  -wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed() (no-hg46 !)
  -wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or orphan()^) and not closed() (hg46 !)
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or unstable()^) and not closed() and not (fxheads() - date(-90)) (no-hg46 !)
  +wip = (parents(not public()) or not public() or . or (head() and branch(default))) and (not obsolete() or orphan()^) and not closed() and not (fxheads() - date(-90)) (hg46 !)
   [templates]
   wip = '{label("wip.branch", if(branches,"{branches} "))}{label(ifeq(graphnode,"x","wip.obsolete","wip.{phase}"),"{rev}:{node|short}")}{label("wip.user", " {author|user}")}{label("wip.tags", if(tags," {tags}"))}{label("wip.tags", if(fxheads," {fxheads}"))}{if(bookmarks," ")}{label("wip.bookmarks", if(bookmarks,bookmarks))}{label(ifcontains(rev, revset("parents()"), "wip.here"), " {desc|firstline}")}'
   [color]
  
  Write changes to hgrc file (Yn)?  y


