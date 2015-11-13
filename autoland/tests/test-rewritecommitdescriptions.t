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

We handle unicode commit descriptions properly

  $ echo foo >> foo
  $ hg commit -m 'bug 1 - stuff'
  $ PARENT=`hg log -r "parents(.)" --template "{node|short}"`
  $ REV=`hg log -r . --template "{node|short}"`
  $ cat > descriptions.json << EOF
  > {"$REV": "bug 1 - こんにちは", "$PARENT": "root commit"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  not rewriting 3a9f6899ef84 - description unchanged
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/599eee383634-92f1368e-replacing.hg (glob)

  $ hg --encoding utf-8 log
  changeset:   1:ca7347cc56f1
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf (esc)
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  
