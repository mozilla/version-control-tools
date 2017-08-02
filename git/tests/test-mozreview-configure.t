#require mozreviewdocker

  $ . $TESTDIR/git/tests/helpers.sh
  $ commonenv

  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -r .
  $ hg -q push --noreview
  $ cd ..

  $ defaultkey=`mozreview create-api-key default@example.com`

  $ alias configure='git mozreview configure --mercurial-url ${MERCURIAL_URL} --bugzilla-url ${BUGZILLA_URL}'

Create autoreview repo manifest

  $ mozreview exec hgrb /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/autoreview createrepomanifest ${MERCURIAL_URL} ssh://${HGSSH_HOST}:${HGSSH_PORT}/
  96ee1d7354c4ad7372047672c36a1f561e3a6a4c http://$DOCKER_HOSTNAME:$HGPORT/test-repo ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo

  $ git -c fetch.prune=true clone hg::${MERCURIAL_URL}test-repo gitrepo
  Cloning into 'gitrepo'...
  $ cd gitrepo
  $ cat > .git/hgrc << EOF
  > [ui]
  > interactive = true
  > promptecho = true
  > EOF

  $ configure << EOF
  > default@example.com
  > ${defaultkey}
  > mynick
  > EOF
  MozReview uses Bugzilla credentials to communicate with servers. These credentials will be stored in your .git/config file in plain text.
  
  Enter your Bugzilla username / e-mail address: default@example.com
  
  A Bugzilla API Key is used to authenticate communication. To generate an API Key, go to http://$DOCKER_HOSTNAME:$HGPORT2/userprefs.cgi?tab=apikey
  
  Enter a Bugzilla API Key: * (glob)
  
  A nickname must be attached to submitted reviews. (IRC nicknames are typically used)
  
  Enter a nickname: mynick
  
  searching for appropriate review repository...
  using hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  installing commit-msg hook

commit-msg hook installed

  $ ls .git/hooks/commit-msg
  .git/hooks/commit-msg

the hook is executable

  $ test -x .git/hooks/commit-msg

"git mozreview" replaced with the full path to "git-mozreview"

  $ grep git-mozreview .git/hooks/commit-msg
  */git/commands/git-mozreview commit-msg-hook "$@" (glob)

We should have created a config file

  $ cat .git/mozreviewconfigversion
  1

Running again should no-op

  $ configure

Configuring when an existing commit-msg hook is installed will issue a warning

  $ rm -f .git/hooks/commit-msg
  $ cat > .git/hooks/commit-msg << EOF
  > #!/bin/sh
  > echo 'dummy hook'
  > exit 1
  > EOF

  $ configure
  warning: existing commit-msg hook does not appear related to MozReview; unable to install custom hook
  (MozReview may lose track of commits when rewriting)

Configuring with an existing old configuration using a git remote will issue a warning

  $ rm -f .git/hooks/commit-msg
  $ git config mozreview.remote foo
  $ git remote add foo hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  $ configure
  warning: will not need the "foo" remote anymore;
  You may remove it with `git remote remove foo`.
  installing commit-msg hook
  $ git config mozreview.remote
  hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo

Cleanup

  $ mozreview stop
  stopped 9 containers
