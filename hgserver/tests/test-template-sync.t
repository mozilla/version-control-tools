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
  applying patch json.patch
  applying patch from stdin
  applying patch logo.patch
  applying patch from stdin
  applying patch pushlog-header.patch
  applying patch from stdin
  applying patch missing-graph-link.patch
  applying patch from stdin
  applying patch link-atom.patch
  applying patch from stdin
  applying patch style-elements.patch
  applying patch from stdin
  applying patch advertise-deployment.patch
  applying patch from stdin
  applying patch summary.patch
  applying patch from stdin
  applying patch notfound.patch
  applying patch from stdin
  applying patch index.patch
  applying patch from stdin
  applying patch firefoxreleases2.patch
  applying patch from stdin
  applying patch changeset-metadata.patch
  applying patch from stdin
  applying patch filename-links.patch
  applying patch from stdin
  applying patch misc.patch
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
  diff -r * -r * hgtemplates/gitweb_mozilla/fileannotate.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/fileannotate.tmpl	Wed Jul 25 14:00:43 2018 -0700
  +++ b/hgtemplates/gitweb_mozilla/fileannotate.tmpl	Thu Jan 01 00:00:00 1970 +0000
  @@ -69,7 +69,6 @@
   <div class="page_path description">{desc|strip|escape|websub|nonempty}</div>
   
   {diffoptsform}
  -
   <script type="text/javascript"{if(nonce, ' nonce="{nonce}"')}>
       renderDiffOptsForm();
   </script>
  diff -r * -r * hgtemplates/gitweb_mozilla/index.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/index.tmpl	Wed Jul 25 14:00:43 2018 -0700
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
   
  diff -r * -r * hgtemplates/gitweb_mozilla/summary.tmpl (glob)
  --- a/hgtemplates/gitweb_mozilla/summary.tmpl	Wed Jul 25 14:00:43 2018 -0700
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

Produce a patch file with differences so we can more easily turn them into
patches.

  $ hg export > $TESTDIR/hgtemplates/.patches/DIFFERENCES
