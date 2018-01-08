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
  rev: 10f03055d22c06f845293434e34419fb5ba53e11 -> 10f03055d22c06f845293434e34419fb5ba53e11
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
  rev: 599eee38363483a76601b414529bfa11973eb87b -> a1dea3050632c11ccc4dbbb5a9519d44744f3b96
  rev: 10f03055d22c06f845293434e34419fb5ba53e11 -> 99d16379ed198d7494b7e60e2edf0696d7a16fdf

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
  rev: 99d16379ed198d7494b7e60e2edf0696d7a16fdf -> 2c6f2ddf672a914719a61fd3158c791c52a469d9

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

  $ echo foo >> foo
  $ hg commit -m 'bug 1 - even more stuff'
  $ hg --encoding utf-8 log
  changeset:   3:cf50de63cf42
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - even more stuff
  
  changeset:   2:2c6f2ddf672a
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
  
  $ cat > descriptions.json <<EOF
  > {
  > "a1dea3050632": "bug 1 - stuff++",
  > "2c6f2ddf672a": "bug 1 - partial rewrite is ok"
  > }
  > EOF
  $ hg rewritecommitdescriptions --descriptions descriptions.json .
  saved backup bundle to $TESTTMP/clone/.hg/strip-backup/cf50de63cf42-a795aa5f-replacing.hg (glob)
  rev: a1dea3050632c11ccc4dbbb5a9519d44744f3b96 -> a1dea3050632c11ccc4dbbb5a9519d44744f3b96
  rev: 2c6f2ddf672a914719a61fd3158c791c52a469d9 -> 515eca0c4333b08596f1f46247e645705438c371

  $ hg --encoding utf-8 log
  changeset:   3:404a56cc02c8
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bug 1 - even more stuff
  
  changeset:   2:515eca0c4333
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
  
