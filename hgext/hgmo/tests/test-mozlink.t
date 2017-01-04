  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -l - << EOF
  > bug 1 - summary line
  > 
  > bug 123456
  > 
  > ab4665521e2f
  > 
  > Aug 2008
  > 
  > b=#12345
  > 
  > GECKO_191a2_20080815_RELBRANCH
  > 
  > 12345 is a bug
  > 
  > foo 123456 whitespace!
  > EOF

  $ hg log -T '{desc|mozlink}\n'
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1">bug 1</a> - summary line
  
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">bug 123456</a>
  
  ab4665521e2f
  
  Aug 2008
  
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345">b=#12345</a>
  
  GECKO_191a2_20080815_RELBRANCH
  
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345">12345</a> is a bug
  
  foo <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">123456</a> whitespace!

  $ echo 1 > foo
  $ hg commit -A -l - << EOF
  > bug 124562 - fix a thing
  > 
  > Fixes #32 and #462
  > 
  > Source-Repo: https://github.com/mozilla/foo
  > EOF

  $ hg log -r . -T '{desc|mozlink}\n'
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=124562">bug 124562</a> - fix a thing
  
  Fixes <a href="https://github.com/mozilla/foo/issues/32">#32</a> and <a href="https://github.com/mozilla/foo/issues/462">#462</a>
  
  Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>

  $ cd ..

The mozlink filter requires context from the full commit message to work properly.
If the firstline filter runs before it, it lacks this context. This is a quick
static analysis check that "mozlink" comes before "firstline".

  $ cat >> checktemplate.py << EOF
  > import os, sys
  > for path in sys.stdin:
  >     path = path.rstrip()
  >     lines = open(path, 'rb').readlines()
  >     for i, line in enumerate(lines):
  >         if 'mozlink' in line and 'firstline' in line:
  >             if line.index('firstline') < line.index('mozlink'):
  >                 relpath = os.path.relpath(path, os.environ['TESTDIR'])
  >                 print('%s:%d has firstline before mozlink' % (relpath, i + 1))
  > EOF

  $ find $TESTDIR/hgtemplates -type f | $PYTHON checktemplate.py
