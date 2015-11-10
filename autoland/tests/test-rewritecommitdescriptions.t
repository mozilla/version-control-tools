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
  $ hg commit --encoding utf-8 -m 'さなフォン丸'
  $ REV=`hg log -r . --template "{node|short}"`
  $ cat > descriptions.json << EOF
  > {"$REV": "💩💩💩"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/1ba51b95d567-0656c233-replacing.hg (glob)

  $ hg --encoding utf-8 log
  changeset:   1:534c3b1cdc6d
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     💩💩💩
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  
