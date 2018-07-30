  $ . $TESTDIR/hgext/firefoxreleases/tests/helpers.sh
  $ enable_extension
  $ start_server
  listening at http://localhost:$HGPORT/ (bound to $LOCALIP:$HGPORT) (?)

Page showing table of Firefox releases is available

  $ http --header content-type http://localhost:$HGPORT/firefoxreleases
  200
  content-type: text/html; charset=ascii
  
  <?xml version="1.0" encoding="ascii"?>
  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US" lang="en-US">
  <head>
  <link rel="icon" href="/static/hgicon.png" type="image/png" />
  <meta name="robots" content="index, nofollow"/>
  <link rel="stylesheet" href="/static/style-gitweb.css" type="text/css" />
  
  <style type="text/css">
  div.feed {
    float: right;
  }
  a img {
    border-width: 0px;
  }
  div.log_link {
    width: 80px;
    background-color: white;
  }
  
  div.log_body {
    padding-left: 96px;
  }
  </style>
  <script type="text/javascript" src="/static/mercurial.js"></script>
  
  <title>$TESTTMP/server: Firefox Releases</title>
  <link rel="alternate" type="application/atom+xml"
     href="/atom-log" title="Atom feed for $TESTTMP/server"/>
  <link rel="alternate" type="application/rss+xml"
     href="/rss-log" title="RSS feed for $TESTTMP/server"/>
  </head>
  <body>
  
  <div class="page_header">
  <div class="logo">
      <a href="https://mercurial-scm.org/">
          <img src="/static/moz-logo-bw-rgb.svg" alt="mercurial" />
      </a>
  </div>
  <a href="/">Mercurial</a>  / firefoxreleases
  </div>
  
  <div class="page_nav">
  <div>
  <a href="/summary">summary</a> |
  <a href="/shortlog">shortlog</a> |
  <a href="/log">changelog</a> |
  <a href="/pushloghtml">pushlog</a> |
  <a href="/graph">graph</a> |
  <a href="/tags">tags</a> |
  <a href="/bookmarks">bookmarks</a> |
  <a href="/branches">branches</a> |
  <a href="/file">files</a> |
  <a href="/help">help</a>
  </div>
  
  <div class="search">
  <form id="searchform" action="/log">
  
  <input name="rev" type="text" value="" size="40" />
  <div id="hint">Find changesets by keywords (author, files, the commit message), revision
  number or hash, or <a href="/help/revsets">revset expression</a>.</div>
  </form>
  </div>
  </div>
  
  <div class="page_body">
  <table border="0">
  <tr>
    <th>Revision</th>
    <th>Build ID</th>
    <th>Channel</th>
    <th>Platform</th>
    <th>Version</th>
    <th>Files</th>
  </tr>
  <tr id="4e0f86874d25nightlylinux6420170527000000" class="parityparity0">
  <td class="firefoxreleasefixed"><a href="/rev/4e0f86874d2556a19bcb5b6d090d24a720229178">4e0f86874d25</a></td>
  <td class="firefoxreleasefixed">20170527000000</td>
  <td>nightly</td>
  <td>linux64</td>
  <td>57.0a1</td>
  <td><a href="https://example.com/build2/">files</a></td>
  </tr><tr id="dc94f7af4edanightlywin6420170527000000" class="parityparity1">
  <td class="firefoxreleasefixed"><a href="/rev/dc94f7af4edae241d4382901b48cb67e43c445e1">dc94f7af4eda</a></td>
  <td class="firefoxreleasefixed">20170527000000</td>
  <td>nightly</td>
  <td>win64</td>
  <td>56.0a1</td>
  <td><a href="https://example.com/build1/">files</a></td>
  </tr><tr id="94086d65796fnightlywin3220170526000000" class="parityparity0">
  <td class="firefoxreleasefixed"><a href="/rev/94086d65796fd7fc8f957a2c5548db17a13f1f1f">94086d65796f</a></td>
  <td class="firefoxreleasefixed">20170526000000</td>
  <td>nightly</td>
  <td>win32</td>
  <td>55.0a1</td>
  <td><a href="https://example.com/build0/">files</a></td>
  </tr>
  </table>
  </div>
  
  <div class="page_footer">
  <div class="page_footer_text">$TESTTMP/server</div>
  <div class="page_footer_text" style="padding-left: 10px">Deployed from <a href="https://hg.mozilla.org/hgcustom/version-control-tools/rev/VCTNODE">VCTNODE</a> at DEPLOYDATE.</div>
  <div class="rss_logo">
  <a href="/rss-log">RSS</a>
  <a href="/atom-log">Atom</a>
  </div>
  <br />
  
  </div>
  </body>
  </html>
  
  

JSON view works

  $ http --header content-type http://localhost:$HGPORT/json-firefoxreleases
  200
  content-type: application/json
  
  {
  "builds": [{
  "node": "4e0f86874d2556a19bcb5b6d090d24a720229178",
  "buildid": "20170527000000",
  "channel": "nightly",
  "platform": "linux64",
  "app_version": "57.0a1",
  "files_url": "https://example.com/build2/"
  }, {
  "node": "dc94f7af4edae241d4382901b48cb67e43c445e1",
  "buildid": "20170527000000",
  "channel": "nightly",
  "platform": "win64",
  "app_version": "56.0a1",
  "files_url": "https://example.com/build1/"
  }, {
  "node": "94086d65796fd7fc8f957a2c5548db17a13f1f1f",
  "buildid": "20170526000000",
  "channel": "nightly",
  "platform": "win32",
  "app_version": "55.0a1",
  "files_url": "https://example.com/build0/"
  }]
  }

Can filter by platform

  $ http --header content-type http://localhost:$HGPORT/json-firefoxreleases?platform=win32
  200
  content-type: application/json
  
  {
  "builds": [{
  "node": "94086d65796fd7fc8f957a2c5548db17a13f1f1f",
  "buildid": "20170526000000",
  "channel": "nightly",
  "platform": "win32",
  "app_version": "55.0a1",
  "files_url": "https://example.com/build0/"
  }]
  }

Confirm no errors in log

  $ cat ./server/error.log
