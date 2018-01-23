#require bmodocker
  $ $TESTDIR/d0cker start-bmo bzexport-test-newbug $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://$DOCKER_HOSTNAME:$HGPORT/

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

Initialize a repo.

  $ mkdir repo
  $ cd repo
  $ hg init

Create some sample bugs.

  $ hg newbug -C 'Firefox :: General' --title 'Stuff is broken' -c 'No good'
  Refreshing configuration cache for http://$DOCKER_HOSTNAME:$HGPORT/bzapi/
  Using default version 'unspecified' of product Firefox
  Created bug 1 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=1
  $ hg newbug -C 'Firefox :: General' --title 'More stuff is broken' -c 'No good'
  Using default version 'unspecified' of product Firefox
  Created bug 2 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=2

Make a patch queue.

  $ touch file.txt
  $ hg add file.txt
  $ hg qnew patch1 -m 'patch1 description'
  $ touch file2.txt
  $ hg add file2.txt
  $ hg qnew patch2 -m 'patch2 description'

Export the top patch and verify patch rename and commit message update.

  $ hg bzexport 1
  patch2 uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=1&action=edit
  $ hg qseries -v
  0 A patch1
  1 A bug-1-patch2
  $ hg log -r . --template '{desc}\n'
  Bug 1 - patch2 description

Export the bottom patch and verify patch rename and *lack* of commit message
update (because bzexport only updates qtip commit messages.)

  $ hg bzexport patch1 2
  skipping update of non-qtip patch
  patch1 uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=2&action=edit
  $ hg qseries -v
  0 A bug-2-patch1
  1 A bug-1-patch2
  $ hg log -r qbase --template '{desc}\n'
  patch1 description
  $ hg log -r . --template '{desc}\n'
  Bug 1 - patch2 description
