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
  abort: No commits found to be rewritten.
  [255]
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
  rev: 10f03055d22c -> 10f03055d22c
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
  rev: 599eee383634 -> a1dea3050632
  rev: 10f03055d22c -> 99d16379ed19

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
  

We handle long sha1s properly

  $ REV=`hg log -r . --template "{node}"`
  $ cat > descriptions.json << EOF
  > {"$REV": "bug 1 - long sha1 is ok"}
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/99d16379ed19-6e1da412-replacing.hg (glob)
  rev: 99d16379ed19 -> 2c6f2ddf672a

  $ hg --encoding utf-8 log
  changeset:   2:2c6f2ddf672a
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - long sha1 is ok
  
  changeset:   1:a1dea3050632
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - stuff++
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  
We handle partial rewrites properly

  $ cat > descriptions.json <<EOF
  > {
  > "a1dea3050632": "bug 1 - stuff++",
  > "2c6f2ddf672a": "bug 1 - partial rewrite is ok"
  > }
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/2c6f2ddf672a-c8370839-replacing.hg (glob)
  rev: a1dea3050632 -> a1dea3050632
  rev: 2c6f2ddf672a -> 515eca0c4333

  $ hg --encoding utf-8 log
  changeset:   2:515eca0c4333
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - partial rewrite is ok
  
  changeset:   1:a1dea3050632
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - stuff++
  
  changeset:   0:3a9f6899ef84
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root commit
  
