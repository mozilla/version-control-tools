  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > reviewboard = $TESTDIR/hgext/reviewboard/client.py
  > EOF
  $ hg init foo
  the MozReview service has been disabled; stop loading the reviewboard/mozreview extension from your hgrc files to make this warning go away
