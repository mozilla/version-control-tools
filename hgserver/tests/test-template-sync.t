This test verifies that all our patches to the gitweb template apply cleanly
and exactly produce the gitweb_mozilla template.

Create a repo so we can test differences against v-c-t

  $ hg init templates
  $ cd templates

Run script to apply our templates changes

  $ $TESTDIR/hgtemplates/.patches/mozify-templates.py \
  >   $TESTDIR/venv/mercurials/4.5.3/lib/python2.7/site-packages/mercurial/templates \
  >   $TESTDIR/hgtemplates \
  >   `pwd`/hgtemplates
  adding atom/bookmarkentry.tmpl
  adding atom/bookmarks.tmpl
  adding atom/branchentry.tmpl
  adding atom/branches.tmpl
  adding atom/changelog.tmpl
  adding atom/changelogentry.tmpl
  adding atom/error.tmpl
  adding atom/filelog.tmpl
  adding atom/header.tmpl
  adding atom/map
  adding atom/pushlog.tmpl
  adding atom/pushlogentry.tmpl
  adding atom/tagentry.tmpl
  adding atom/tags.tmpl
  adding gitweb/bookmarks.tmpl
  adding gitweb/branches.tmpl
  adding gitweb/changelog.tmpl
  adding gitweb/changelogentry.tmpl
  adding gitweb/changeset.tmpl
  adding gitweb/error.tmpl
  adding gitweb/fileannotate.tmpl
  adding gitweb/filecomparison.tmpl
  adding gitweb/filediff.tmpl
  adding gitweb/filelog.tmpl
  adding gitweb/filerevision.tmpl
  adding gitweb/footer.tmpl
  adding gitweb/graph.tmpl
  adding gitweb/graphentry.tmpl
  adding gitweb/header.tmpl
  adding gitweb/help.tmpl
  adding gitweb/helptopics.tmpl
  adding gitweb/index.tmpl
  adding gitweb/manifest.tmpl
  adding gitweb/map
  adding gitweb/notfound.tmpl
  adding gitweb/search.tmpl
  adding gitweb/shortlog.tmpl
  adding gitweb/summary.tmpl
  adding gitweb/tags.tmpl
  adding gitweb_mozilla/bookmarks.tmpl
  adding gitweb_mozilla/branches.tmpl
  adding gitweb_mozilla/changelog.tmpl
  adding gitweb_mozilla/changelogentry.tmpl
  adding gitweb_mozilla/changeset.tmpl
  adding gitweb_mozilla/error.tmpl
  adding gitweb_mozilla/fileannotate.tmpl
  adding gitweb_mozilla/filecomparison.tmpl
  adding gitweb_mozilla/filediff.tmpl
  adding gitweb_mozilla/filelog.tmpl
  adding gitweb_mozilla/filerevision.tmpl
  adding gitweb_mozilla/firefoxreleases.tmpl
  adding gitweb_mozilla/footer.tmpl
  adding gitweb_mozilla/graph.tmpl
  adding gitweb_mozilla/graphentry.tmpl
  adding gitweb_mozilla/header.tmpl
  adding gitweb_mozilla/help.tmpl
  adding gitweb_mozilla/helptopics.tmpl
  adding gitweb_mozilla/index.tmpl
  adding gitweb_mozilla/manifest.tmpl
  adding gitweb_mozilla/map
  adding gitweb_mozilla/notfound.tmpl
  adding gitweb_mozilla/pushlog.tmpl
  adding gitweb_mozilla/repoinfo.tmpl
  adding gitweb_mozilla/search.tmpl
  adding gitweb_mozilla/shortlog.tmpl
  adding gitweb_mozilla/summary.tmpl
  adding gitweb_mozilla/tags.tmpl
  adding json/changelist.tmpl
  adding json/graph.tmpl
  adding json/map
  adding map-cmdline.bisect
  adding map-cmdline.changelog
  adding map-cmdline.compact
  adding map-cmdline.default
  adding map-cmdline.phases
  adding map-cmdline.show
  adding map-cmdline.status
  adding map-cmdline.xml
  adding paper/bookmarks.tmpl
  adding paper/branches.tmpl
  adding paper/changeset.tmpl
  adding paper/diffstat.tmpl
  adding paper/error.tmpl
  adding paper/fileannotate.tmpl
  adding paper/filecomparison.tmpl
  adding paper/filediff.tmpl
  adding paper/filelog.tmpl
  adding paper/filelogentry.tmpl
  adding paper/filerevision.tmpl
  adding paper/footer.tmpl
  adding paper/graph.tmpl
  adding paper/graphentry.tmpl
  adding paper/header.tmpl
  adding paper/help.tmpl
  adding paper/helptopics.tmpl
  adding paper/index.tmpl
  adding paper/manifest.tmpl
  adding paper/map
  adding paper/notfound.tmpl
  adding paper/search.tmpl
  adding paper/shortlog.tmpl
  adding paper/shortlogentry.tmpl
  adding paper/tags.tmpl
  adding raw/changelog.tmpl
  adding raw/changeset.tmpl
  adding raw/error.tmpl
  adding raw/fileannotate.tmpl
  adding raw/filediff.tmpl
  adding raw/graph.tmpl
  adding raw/graphedge.tmpl
  adding raw/graphnode.tmpl
  adding raw/index.tmpl
  adding raw/logentry.tmpl
  adding raw/manifest.tmpl
  adding raw/map
  adding raw/notfound.tmpl
  adding raw/search.tmpl
  adding rss/bookmarkentry.tmpl
  adding rss/bookmarks.tmpl
  adding rss/branchentry.tmpl
  adding rss/branches.tmpl
  adding rss/changelog.tmpl
  adding rss/changelogentry.tmpl
  adding rss/error.tmpl
  adding rss/filelog.tmpl
  adding rss/filelogentry.tmpl
  adding rss/header.tmpl
  adding rss/map
  adding rss/tagentry.tmpl
  adding rss/tags.tmpl
  adding static/coal-file.png
  adding static/coal-folder.png
  adding static/feed-icon-14x14.png
  adding static/followlines.js
  adding static/hgicon.png
  adding static/hglogo.png
  adding static/jquery-1.2.6.min.js
  adding static/livemarks16.png
  adding static/mercurial.js
  adding static/moz-logo-bw-rgb.svg
  adding static/style-gitweb.css
  adding static/style-paper.css
  adding static/style.css
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/bookmarks.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/bookmarks.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/branches.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/branches.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/changelog.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/changeset.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/changeset.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/error.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/error.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/fileannotate.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/fileannotate.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filecomparison.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filecomparison.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filediff.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filediff.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filelog.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filelog.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filerevision.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/filerevision.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/graph.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/graph.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/help.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/help.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/helptopics.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/helptopics.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/index.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/manifest.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/manifest.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/notfound.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/search.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/search.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/shortlog.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/shortlog.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/summary.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/summary.tmpl
  replacing b'<a href="{logourl}" titl'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/tags.tmpl
  replacing b'<a href="{url|urlescape}'... in $TESTTMP/templates/hgtemplates/gitweb_mozilla/tags.tmpl
  committing automated transformations
  applying patch atom.patch
  applying patch from stdin
  applying patch firefoxreleases.patch
  applying patch from stdin
  patching file hgtemplates/json/map
  Hunk #1 succeeded at 54 with fuzz 2 (offset 17 lines).
  applying patch json.patch
  applying patch from stdin
  applying patch logo.patch
  applying patch from stdin

And replace the working directory with what is in this repository, modulo the
patches.

  $ rm -rf hgtemplates
  $ cp -R $TESTDIR/hgtemplates/ .

But not the patches themselves

  $ rm -rf hgtemplates/.patches

And compare what the patches produced versus what's in v-c-t

  $ hg commit -A -m 'v-c-t version'

  $ hg diff -c .
  diff -r * -r * hgtemplates/gitweb_mozilla/changelog.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/changelog.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/changelog.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -21,6 +21,7 @@
   <a href="{url|urlescape}summary{sessionvars%urlparameter}">summary</a> |
   <a href="{url|urlescape}shortlog/{symrev}{sessionvars%urlparameter}">shortlog</a> |
   changelog |
  +<a href="{url|urlescape}pushloghtml{sessionvars%urlparameter}">pushlog</a> |
   <a href="{url|urlescape}graph/{symrev}{sessionvars%urlparameter}">graph</a> |
   <a href="{url|urlescape}tags{sessionvars%urlparameter}">tags</a> |
   <a href="{url|urlescape}bookmarks{sessionvars%urlparameter}">bookmarks</a> |
  diff -r * -r * hgtemplates/gitweb_mozilla/changelogentry.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/changelogentry.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/changelogentry.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,16 +1,15 @@
  -<div>
  - <a class="title" href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">
  -  <span class="age">{date|rfc822date}</span>
  -  {desc|strip|firstline|escape|nonempty}
  -  {alltags}
  - </a>
  +<div class="title">
  +{node|short}: {desc|strip|firstline|escape}
  +{alltags}
   </div>
   <div class="title_text">
   <div class="log_link">
  -<a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">changeset</a><br/>
  +<a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">diff</a><br/>
  +<a href="{url|urlescape}file/{node|short}{sessionvars%urlparameter}">browse</a>
   </div>
  -<i>{author|obfuscate} [{date|rfc822date}] rev {rev}</i><br/>
  +<cite>{author|obfuscate}</cite> - {date|rfc822date} - rev {rev}<br/>
  +{if(pushid, 'Push <a href="{url|urlescape}pushloghtml?changeset={node|short}">{pushid}</a> by {pushuser|escape} at {pushdate|isodate}<br />')}
   </div>
  -<div class="log_body description">{desc|strip|escape|websub|nonempty}
  +<div class="log_body description">{desc|strip|escape|mozlink}
   
   </div>
  diff -r * -r * hgtemplates/gitweb_mozilla/changeset.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/changeset.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/changeset.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -13,7 +13,7 @@
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
   </div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / changeset
  +<a href="/">Mercurial</a> {pathdef%breadcrumb} / changeset / {node|short} {if(backedoutbynode, '&#x2620;')}
   </div>
   
   <div class="page_nav">
  @@ -34,14 +34,13 @@
   {searchform}
   </div>
   
  -<div>
  - <a class="title" href="{url|urlescape}raw-rev/{node|short}">
  -  {desc|strip|escape|firstline|nonempty}
  -  {alltags}
  - </a>
  +<div class="title">
  +{desc|strip|escape|mozlink|firstline|nonempty}
  +{alltags}
   </div>
   <div class="title_text">
   <table cellspacing="0">
  +{if(backedoutbynode, '<tr><td colspan="2" style="background:#ff3333;"><strong>&#x2620;&#x2620; backed out by <a style="font-family: monospace" href="{url|urlescape}rev/{backedoutbynode|short}">{backedoutbynode|short}</a> &#x2620; &#x2620;</strong></td></tr>')}
   <tr><td>author</td><td>{author|obfuscate}</td></tr>
   <tr><td></td><td class="date age">{date|rfc822date}</td></tr>
   {branch%changesetbranch}
  @@ -52,9 +51,24 @@
   {if(obsolete, '<tr><td>obsolete</td><td>{succsandmarkers%obsfateentry}</td></tr>')}
   {ifeq(count(parent), '2', parent%changesetparentdiff, parent%changesetparent)}
   {child%changesetchild}
  +<tr><td>push id</td><td>{if(pushid, '<a href="{url|urlescape}pushloghtml?changeset={node|short}">{pushid}</a>', 'unknown')}</td></tr>
  +<tr><td>push user</td><td>{if(pushuser, pushuser|escape, 'unknown')}</td></tr>
  +<tr><td>push date</td><td>{if(pushdate, pushdate|isodate, 'unknown')}</td></tr>
  +{if(convertsourcepath, '<tr><td>converted from</td><td><a href="{convertsourcepath}/rev/{convertsourcenode}">{convertsourcenode}</a></td></tr>')}
  +{if(treeherderrepourl, if(pushhead, '<tr><td>treeherder</td><td>{treeherderrepo|escape}@{pushhead|short} [<a href="{treeherderrepourl}&revision={pushhead}">default view</a>] [<a href="{treeherderrepourl}&revision={pushhead}&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>'))}
  +{if(perfherderurl, '<tr><td>perfherder</td><td>[<a href="{perfherderurl}&framework=1" target="_blank">talos</a>] [<a href="{perfherderurl}&framework=2" target="_blank">build metrics</a>] [<a href="{perfherderurl}&framework=6" target="_blank">platform microbench</a>] (compared to previous push)</td></tr>')}
  +{if(reviewers, '<tr><td>reviewers</td><td>{join(reviewers%reviewerlink, ", ")}</td></tr>')}
  +{if(bugs, '<tr><td>bugs</td><td>{join(bugs%bughyperlink, ", ")}</td></tr>')}
  +{if(milestone, '<tr><td>milestone</td><td>{milestone|escape}</td></tr>')}
  +{if(backsoutnodes, '<tr><td>backs out</td><td>{join(backsoutnodes%backedoutnodelink, "<br />")}</td></tr>')}
  +{if(have_first_and_last_firefox_releases, '
  +  <tr><td>first release with</td><td><div>{firefox_releases_first % firefox_release_entry}</div></td></tr>
  +  <tr><td>last release without</td><td><div>{firefox_releases_last % firefox_release_entry}</div></td></tr>
  +  ')}
  +{if(firefox_releases_here, '<tr><td>releases</td><td><div>{firefox_releases_here % firefox_release_entry_here}</div></td></tr>')}
   </table></div>
   
  -<div class="page_body description">{desc|strip|escape|websub|nonempty}</div>
  +<div class="page_body description">{desc|strip|escape|mozlink}</div>
   <div class="list_head"></div>
   <div class="title_text">
   <table cellspacing="0">
  diff -r * -r * hgtemplates/gitweb_mozilla/error.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/error.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/error.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -22,6 +22,7 @@
   <a href="{url|urlescape}shortlog{sessionvars%urlparameter}">shortlog</a> |
   <a href="{url|urlescape}log{sessionvars%urlparameter}">changelog</a> |
   <a href="{url|urlescape}pushloghtml{sessionvars%urlparameter}">pushlog</a> |
  +<a href="{url|urlescape}graph{sessionvars%urlparameter}">graph</a> |
   <a href="{url|urlescape}tags{sessionvars%urlparameter}">tags</a> |
   <a href="{url|urlescape}bookmarks{sessionvars%urlparameter}">bookmarks</a> |
   <a href="{url|urlescape}branches{sessionvars%urlparameter}">branches</a> |
  diff -r * -r * hgtemplates/gitweb_mozilla/fileannotate.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/fileannotate.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/fileannotate.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -13,7 +13,7 @@
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
   </div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / annotate
  +<a href="/">Mercurial</a> {pathdef%breadcrumb} / annotate / {file|escape}
   </div>
   
   <div class="page_nav">
  @@ -69,7 +69,6 @@
   <div class="page_path description">{desc|strip|escape|websub|nonempty}</div>
   
   {diffoptsform}
  -
   <script type="text/javascript"{if(nonce, ' nonce="{nonce}"')}>
       renderDiffOptsForm();
   </script>
  diff -r * -r * hgtemplates/gitweb_mozilla/filediff.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/filediff.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/filediff.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -13,7 +13,7 @@
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
   </div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / diff
  +<a href="/">Mercurial</a> {pathdef%breadcrumb} / diff / {file|escape}
   </div>
   
   <div class="page_nav">
  diff -r * -r * hgtemplates/gitweb_mozilla/filelog.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/filelog.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/filelog.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,5 @@
   {header}
  -<title>{repo|escape}: File revisions</title>
  +<title>{repo|escape}: File revisions: {file|escape}</title>
   <link rel="alternate" type="application/atom+xml"
      href="{url|urlescape}atom-log" title="Atom feed for {repo|escape}"/>
   <link rel="alternate" type="application/rss+xml"
  @@ -13,7 +13,7 @@
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
   </div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / file revisions
  +<a href="/">Mercurial</a> {pathdef%breadcrumb} / file revisions / {file|escape}
   </div>
   
   <div class="page_nav">
  @@ -31,7 +31,7 @@
   <a href="{url|urlescape}annotate/{symrev}/{file|urlescape}{sessionvars%urlparameter}">annotate</a> |
   <a href="{url|urlescape}diff/{symrev}/{file|urlescape}{sessionvars%urlparameter}">diff</a> |
   <a href="{url|urlescape}comparison/{symrev}/{file|urlescape}{sessionvars%urlparameter}">comparison</a> |
  -<a href="{url|urlescape}rss-log/tip/{file|urlescape}">rss</a> |
  +<a href="{url|urlescape}atom-log/{symrev}/{file|urlescape}"><img src="{staticurl}livemarks16.png" alt="Feed" title="Feed of repository changes"/></a>
   <a href="{url|urlescape}help{sessionvars%urlparameter}">help</a>
   <br/>
   {nav%filenav}
  diff -r * -r * hgtemplates/gitweb_mozilla/filerevision.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/filerevision.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/filerevision.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -13,7 +13,7 @@
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
   </div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / file revision
  +<a href="/">Mercurial</a> {pathdef%breadcrumb} / file revision / {file|escape}@{node|short}
   </div>
   
   <div class="page_nav">
  @@ -66,7 +66,7 @@
   </table>
   </div>
   
  -<div class="page_path description">{desc|strip|escape|websub|nonempty}</div>
  +<div class="page_path description">{desc|strip|escape|mozlink|nonempty}</div>
   
   <div class="page_body">
   <pre class="sourcelines stripes"
  diff -r * -r * hgtemplates/gitweb_mozilla/footer.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/footer.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/footer.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,6 @@
   <div class="page_footer">
   <div class="page_footer_text">{repo|escape}</div>
  +<div class="page_footer_text" style="padding-left: 10px">Deployed from <a href="https://hg.mozilla.org/hgcustom/version-control-tools/rev/VCTNODE">VCTNODE</a> at DEPLOYDATE.</div>
   <div class="rss_logo">
   <a href="{url|urlescape}rss-log">RSS</a>
   <a href="{url|urlescape}atom-log">Atom</a>
  diff -r * -r * hgtemplates/gitweb_mozilla/header.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/header.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/header.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,4 +5,21 @@
   <link rel="icon" href="{staticurl|urlescape}hgicon.png" type="image/png" />
   <meta name="robots" content="index, nofollow"/>
   <link rel="stylesheet" href="{staticurl|urlescape}style-gitweb.css" type="text/css" />
  +
  +<style type="text/css">
  +div.feed \{
  +  float: right;
  +}
  +a img \{
  +  border-width: 0px;
  +}
  +div.log_link \{
  +  width: 80px;
  +  background-color: white;
  +}
  +
  +div.log_body \{
  +  padding-left: 96px;
  +}
  +</style>
   <script type="text/javascript" src="{staticurl|urlescape}mercurial.js"></script>
  diff -r * -r * hgtemplates/gitweb_mozilla/index.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/index.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/index.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,10 +5,10 @@
   
   <div class="page_header">
       <div class="logo">
  -    <a href="{logourl}">
  -        <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
  -    </a>
  -</div>
  +        <a href="{logourl}">
  +            <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
  +        </a>
  +    </div>
       <a href="/">Mercurial</a> {pathdef%breadcrumb}
   </div>
   
  @@ -16,13 +16,144 @@
       <tr>
           <td><a href="?sort={sort_name}">Name</a></td>
           <td><a href="?sort={sort_description}">Description</a></td>
  -        <td><a href="?sort={sort_contact}">Contact</a></td>
           <td><a href="?sort={sort_lastchange}">Last modified</a></td>
           <td>&nbsp;</td>
           <td>&nbsp;</td>
       </tr>
       {entries%indexentry}
   </table>
  +&nbsp;
  +&nbsp;
  +&nbsp;
  +<div class="title">
  +     Repository Layout
  +</div>
  +<table cellspacing="0">
  +    <tr>
  +        <td><a href="/">/</a></td>
  +        <td>Mozilla top level repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/automation">automation</a></td>
  +        <td>QA automation projects</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/build">build</a></td>
  +        <td>Build team projects</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/experimental">experimental</a></td>
  +        <td>Playground for version control wizards</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/hgcustom">hgcustom</a></td>
  +        <td>Mercurial customizations</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/incubator">incubator</a></td>
  +        <td>Incubator projects</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/l10n">l10n</a></td>
  +        <td>L10n infrastructure projects</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/l10n-central">l10n-central</a></td>
  +        <td>L10n repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/gaia-l10n">gaia-l10n</a></td>
  +        <td>Gaia L10n repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/labs">labs</a></td>
  +        <td>Mozilla <a href="http://labs.mozilla.com/">labs</a> projects</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/projects">projects</a></td>
  +        <td>Miscellaneous project repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/qa">qa</a></td>
  +        <td>QA projects and functional test repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/integration">integration</a></td>
  +        <td>Source code integration work</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases">releases</a></td>
  +        <td>Release branches (use releases/l10n-branchname for l10n repos)</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v1_2">releases/gaia-l10n/v1_2</a></td>
  +        <td>Gaia l10n v1_2 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v1_3">releases/gaia-l10n/v1_3</a></td>
  +        <td>Gaia l10n v1_3 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v1_4">releases/gaia-l10n/v1_4</a></td>
  +        <td>Gaia l10n v1_4 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v2_0">releases/gaia-l10n/v2_0</a></td>
  +        <td>Gaia l10n v2_0 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v2_1">releases/gaia-l10n/v2_1</a></td>
  +        <td>Gaia l10n v2_1 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v2_2">releases/gaia-l10n/v2_2</a></td>
  +        <td>Gaia l10n v2_2 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/gaia-l10n/v2_5">releases/gaia-l10n/v2_5</a></td>
  +        <td>Gaia l10n v2_5 repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/l10n/mozilla-aurora">releases/l10n/mozilla-aurora</a></td>
  +        <td>Aurora l10n repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/l10n/mozilla-beta">releases/l10n/mozilla-beta</a></td>
  +        <td>Beta l10n repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/releases/l10n/mozilla-release">releases/l10n/mozilla-release</a></td>
  +        <td>Release l10n repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/rewriting-and-analysis">rewriting-and-analysis</a></td>
  +        <td>Rewriting &amp; Analysis</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/SeaMonkey">SeaMonkey</a></td>
  +        <td>The SeaMonkey Project</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/services">services</a></td>
  +        <td>Code related to Mozilla services projects (Firefox sync, etc..)</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/users">users</a></td>
  +        <td>User code repositories</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/weave-l10n">weave-l10n</a></td>
  +        <td>l10n repos for weave code</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/webtools">webtools</a></td>
  +        <td>Webtool projects like mxr, etc</td>
  +    </tr>
  +    <tr>
  +        <td><a href="/www">www</a></td>
  +        <td>Code related to various mozilla websites</td>
  +    </tr>
  +</table>
   <div class="page_footer">
   {motd}
   </div>
  diff -r * -r * hgtemplates/gitweb_mozilla/map (glob)
  --- a/hgtemplates/gitweb_mozilla/map	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/map	Thu Jan 01 00:00:00 1970 +0000
  @@ -23,6 +23,7 @@
   naventry = '<a href="{url|urlescape}log/{node|short}{sessionvars%urlparameter}">{label|escape}</a> '
   navshortentry = '<a href="{url|urlescape}shortlog/{node|short}{sessionvars%urlparameter}">{label|escape}</a> '
   navgraphentry = '<a href="{url|urlescape}graph/{node|short}{sessionvars%urlparameter}">{label|escape}</a> '
  +navpushentry = '<a href="{url|urlescape}pushloghtml/{page}{sessionvars%urlparameter}">{label|escape}</a> '
   filenaventry = '<a href="{url|urlescape}log/{node|short}/{file|urlescape}{sessionvars%urlparameter}">{label|escape}</a> '
   filedifflink = '<a href="{url|urlescape}diff/{node|short}/{file|urlescape}{sessionvars%urlparameter}">{file|escape}</a> '
   filenodelink = '
  @@ -96,7 +97,7 @@
     <a href="#{lineid}"></a><span id="{lineid}">{strip(line|escape, '\r\n')}</span>'
   annotateline = '
     <tr id="{lineid}" style="font-family:monospace" class="parity{parity}{ifeq(node, originalnode, ' thisrev')}">
  -    <td class="annotate linenr parity{blockparity}" style="text-align: right;">
  +    <td class="annotate parity{blockparity}" style="text-align: right;">
         {if(blockhead,
             '<a href="{url|urlescape}annotate/{node|short}/{file|urlescape}{sessionvars%urlparameter}#l{targetline}">
                {rev}
  @@ -105,7 +106,7 @@
           <div>
             <a href="{url|urlescape}annotate/{node|short}/{file|urlescape}{sessionvars%urlparameter}#l{targetline}">
               {node|short}</a>
  -          {desc|escape|firstline}
  +          {desc|escape|mozlink|firstline}
           </div>
           <div><em>{author|obfuscate}</em></div>
           <div>parents: {parents%annotateparent}</div>
  @@ -278,34 +279,34 @@
   obsfateentry = '{obsfateverb}{obsfateoperations}{obsfatesuccessors}'
   shortlogentry = '
     <tr class="parity{parity}">
  -    <td class="age"><i class="age">{date|rfc822date}</i></td>
  -    <td><i>{author|person}</i></td>
  +    <td class="link">
  +      <a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">diff</a><br/>
  +      <a href="{url|urlescape}file/{node|short}{sessionvars%urlparameter}">browse</a>
  +    </td>
  +    <td>{node|short}<br/><i class="age">{date|isodate}</i></td>
       <td>
  -      <a class="list" href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">
  -        <b>{desc|strip|firstline|escape|nonempty}</b>
  -        {alltags}
  -      </a>
  -    </td>
  -    <td class="link" nowrap>
  -      <a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">changeset</a> |
  -      <a href="{url|urlescape}file/{node|short}{sessionvars%urlparameter}">files</a>
  +      <strong><cite>{author|person}</cite> - {desc|strip|escape|mozlink|firstline}</strong>
  +      {alltags}
       </td>
     </tr>'
  +pushinfo = '<cite>{user}<br/><span class="date">{date|date}</span></cite>'
  +mergehidden = '<br/>\xe2\x86\x90 {count} merge changesets <a class="expand hideid{id}" href="#">[Collapse]</a>' (esc)
  +pushlogentry = '<tr class="pushlogentry parity{parity} {hidden} id{id}"><td>{push%pushinfo}</td><td><a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">{node|short}</a></td><td><strong>{author|person} &mdash; {desc|strip|escape|mozlink|firstline|addbreaks}</strong> <span class="logtags">{inbranch%inbranchtag}{branches%branchtag}{tags%tagtag}</span>{mergerollup%mergehidden}</td></tr>\n'
   filelogentry = '
     <tr class="parity{if(patch, '1', '{parity}')}">
  -    <td class="age"><i class="age">{date|rfc822date}</i></td>
  +    <td class="link">
  +      <a href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">diff</a><br/>
  +      <a href="{url|urlescape}file/{node|short}{sessionvars%urlparameter}">browse</a><br/>
  +      <a href="{url|urlescape}annotate/{node|short}/{file|urlescape}{sessionvars%urlparameter}">annotate</a>
  +    </td>
  +    <td>
  +      {node|short}<br/>created <i>{date|isodate}</i>{rename%filelogrename}
  +      {if(pushdate, '<br/>pushed <i>{pushdate|isodate}</i>', '<br/>pushed <i>unknown</i>')}
  +    </td>
       <td><i>{author|person}</i></td>
       <td>
  -      <a class="list" href="{url|urlescape}rev/{node|short}{sessionvars%urlparameter}">
  -        <b>{desc|strip|firstline|escape|nonempty}</b>
  -        {alltags}
  -      </a>
  -    </td>
  -    <td class="link">
  -      <a href="{url|urlescape}file/{node|short}/{file|urlescape}{sessionvars%urlparameter}">file</a> |
  -      <a href="{url|urlescape}diff/{node|short}/{file|urlescape}{sessionvars%urlparameter}">diff</a> |
  -      <a href="{url|urlescape}annotate/{node|short}/{file|urlescape}{sessionvars%urlparameter}">annotate</a>
  -      {rename%filelogrename}
  +      <strong><cite>{author|person}</cite> - {desc|strip|escape|mozlink|firstline}</strong>
  +      {alltags}
       </td>
     </tr>
     {if(patch, '<tr><td colspan="4">{diff}</td></tr>')}'
  @@ -318,8 +319,7 @@
         </a>
       </td>
       <td>{description}</td>
  -    <td>{contact|obfuscate}</td>
  -    <td class="age">{lastchange|rfc822date}</td>
  +    <td class="age">at {lastchange|rfc3339date}</td>
       <td class="indexlinks">{archives%indexarchiveentry}</td>
       <td>{if(isdirectory, '',
               '<div class="rss_logo">
  @@ -359,3 +359,44 @@
       <span>At end of lines:</span>
       <input id="ignorewseol-checkbox" type="checkbox" />
     </form>'
  +
  +pushlog = pushlog.tmpl
  +bughyperlink = '<a href="{url}">{no|escape}</a>'
  +reviewerlink = '<a href="{url|urlescape}log?rev={revset|urlescape}&revcount=50">{name|escape}</a>'
  +backedoutnodelink = '<a style="font-family: monospace" href="{url|urlescape}rev/{node|short}">{node|short}</a>'
  +
  +firefoxreleases = firefoxreleases.tmpl
  +firefoxreleasetableentry = '<tr id="{anchor|escape}" class="parity{parity}">
  +  <td class="firefoxreleasefixed"><a href="{url|urlescape}rev/{revision}{sessionvars%urlparameter}">{revision|short}</a></td>
  +  <td class="firefoxreleasefixed">{build_id|escape}</td>
  +  <td>{channel|escape}</td>
  +  <td>{platform|escape}</td>
  +  <td>{app_version|escape}</td>
  +  <td><a href="{artifacts_url}">files</a></td>
  +  </tr>'
  +
  +# Render a first and last release build entry on the changeset page.
  +firefox_release_entry = '<div class="firefoxreleasecsetentry">
  +    <div>{channel|escape} {platform|escape}</div>
  +    <div class="firefoxreleasecsetdetails">
  +      {ifeq(revision, node, '{revision|short}', '<a href="{url|urlescape}rev/{revision}{sessionvars%urlparameter}">{revision|short}</a>')}
  +      /
  +      {app_version|escape}
  +      /
  +      <a href="{url|urlescape}firefoxreleases{sessionvars%urlparameter}#{anchor}">{build_id|escape}</a>
  +      /
  +      <a href="{artifacts_url}">files</a>
  +    </div></div>'
  +
  +# Render a release build for this changeset.
  +firefox_release_entry_here = '<div class="firefoxreleasecsetentry">
  +    <div>{channel|escape} {platform|escape}</div>
  +    <div class="firefoxreleasecsetdetails">
  +      {app_version|escape}
  +      /
  +      <a href="{url|urlescape}firefoxreleases{sessionvars%urlparameter}#{anchor}">{build_id|escape}</a>
  +      {if(previousnode, '/
  +      <a href="{url|urlescape}pushloghtml?fromchange={previousnode|short}&tochange={node|short}">pushlog to previous</a>')}
  +    </div></div>'
  +
  +repoinfo = repoinfo.tmpl
  diff -r * -r * hgtemplates/gitweb_mozilla/notfound.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/notfound.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/notfound.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -9,7 +9,7 @@
       <a href="{logourl}">
           <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
       </a>
  -</div> Not found: {repo|escape}
  +</div>
   </div>
   
   <div class="page_body">
  diff -r * -r * hgtemplates/gitweb_mozilla/summary.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/summary.tmpl	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/summary.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -8,12 +8,12 @@
   <body>
   
   <div class="page_header">
  -<div class="logo">
  -    <a href="{logourl}">
  -        <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
  -    </a>
  -</div>
  -<a href="/">Mercurial</a> {pathdef%breadcrumb} / summary
  +    <div class="logo">
  +        <a href="{logourl}">
  +            <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />
  +        </a>
  +    </div>
  +    <a href="/">Mercurial</a> {pathdef%breadcrumb} / summary
   </div>
   
   <div class="page_nav">
  @@ -34,8 +34,8 @@
   
   <div class="title">&nbsp;</div>
   <table cellspacing="0">
  -<tr><td>description</td><td>{desc}</td></tr>
  -<tr><td>owner</td><td>{owner|obfuscate}</td></tr>
  +<!--<tr><td>description</td><td>{desc}</td></tr>
  +<tr><td>owner</td><td>{owner|obfuscate}</td></tr>-->
   <tr><td>last change</td><td class="date age">{lastchange|rfc822date}</td></tr>
   </table>
   
  diff -r * -r * hgtemplates/json/map (glob)
  --- a/hgtemplates/json/map	Tue May 29 13:59:58 2018 -0700
  +++ b/hgtemplates/json/map	Thu Jan 01 00:00:00 1970 +0000
  @@ -68,7 +68,9 @@
     "user": {author|utf8|json},
     "phase": {phase|json},
     "parents": [{if(allparents, join(allparents%changesetparent, ", "),
  -                  join(parent%changesetparent, ", "))}]
  +                  join(parent%changesetparent, ", "))}],
  +  "pushid": {pushid|json},
  +  "pushdate": {pushdate|json}
     }'
   graphentry = '\{
     "node": {node|json},
  @@ -84,9 +86,7 @@
     "color": {color|json},
     "edges": {edges|json},
     "parents": [{if(allparents, join(allparents%changesetparent, ", "),
  -                  join(parent%changesetparent, ", "))}],
  -  "pushid": {pushid|json},
  -  "pushdate": {pushdate|json}
  +                  join(parent%changesetparent, ", "))}]
     }'
   changelistentryname = '{name|utf8|json}'
   changeset = '\{
  @@ -102,7 +102,8 @@
     "phase": {phase|json},
     "pushid": {pushid|json},
     "pushdate": {pushdate|json},
  -  "pushuser": {pushuser|json}
  +  "pushuser": {pushuser|json},
  +  "landingsystem": {if(landingsystem, landingsystem|json, "null")}
     }'
   changesetbranch = '{name|utf8|json}'
   changesetbookmark = '{bookmark|utf8|json}'
  @@ -290,3 +291,6 @@
     "app_version": {app_version|json},
     "files_url": {artifacts_url|json}
     }'
  +repoinfo = '\{
  +  "group_owner": {groupowner|json}
  +  }'

Produce a patch file with differences so we can more easily turn them into
patches.

  $ hg export > $TESTDIR/hgtemplates/.patches/DIFFERENCES
