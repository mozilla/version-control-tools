Set up a repo

  $ mkdir clone
  $ cd clone
  $ hg init
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rewritecommitdescriptions = $TESTDIR/autoland/hgext/rewritecommitdescriptions.py
  > EOF

Create some commits to rewrite

  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ echo foo >> foo
  $ hg commit -m 'bug 1 - stuff'
  $ echo foo >> foo
  $ hg commit -m 'bug 1 - more stuff'
  $ PARENT=`hg log -r "parents(.)" --template "{node|short}"`
  $ REV=`hg log -r . --template "{node|short}"`

We handle having no commits which match commit_descriptions properly

  $ cat > descriptions.json << EOF
  > {"42": "non-existent commit"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  not rewriting 10f03055d22c - description unchanged
  no commits found to be rewritten
  base: 10f03055d22c
  $ hg --encoding utf-8 log
  changeset:   2:10f03055d22c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - more stuff
  
  changeset:   1:599eee383634
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - stuff
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  

We handle having no commits to rewrite properly

  $ cat > descriptions.json << EOF
  > {"$REV": "bug 1 - more stuff"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  not rewriting 10f03055d22c - description unchanged
  no commits found to be rewritten
  base: 10f03055d22c
  $ hg --encoding utf-8 log
  changeset:   2:10f03055d22c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - more stuff
  
  changeset:   1:599eee383634
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - stuff
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  

We handle unicode commit descriptions properly

  $ cat > descriptions.json << EOF
  > {"$REV": "bug 1 - こんにちは", "$PARENT": "bug 1 - stuff++"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/10f03055d22c-f5e0148f-replacing.hg (glob)
  base: a1dea3050632

  $ hg --encoding utf-8 log
  changeset:   2:99d16379ed19
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf (esc)
  
  changeset:   1:a1dea3050632
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - stuff++
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  
