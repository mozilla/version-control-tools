#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /enable-fastannotate /repo/hg/mozilla/mozilla-central

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/mozilla-central
  $ cd mozilla-central
  $ cat > foo << EOF
  > line0
  > line1
  > line2
  > line3
  > EOF
  $ hg add foo
  $ hg commit -m 'commit 1'
  $ cat > foo << EOF
  > line0
  > line1 modified
  > line2
  > line3
  > EOF
  $ hg commit -m 'commit 2'
  $ cat > foo << EOF
  > line0
  > line1 modified
  > line2 modified
  > line3
  > EOF
  $ hg commit -m 'commit 3'
  $ hg -q push

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ http ${HGWEB_0_URL}mozilla-central/annotate/f01fe54ccaa1/foo | grep '<pre>'
  <td class="followlines-btn-parent"><pre><a class="linenr" href="#l1">     1</a></pre></td>
  <td><pre>line0
  <td class="followlines-btn-parent"><pre><a class="linenr" href="#l2">     2</a></pre></td>
  <td><pre>line1 modified
  <td class="followlines-btn-parent"><pre><a class="linenr" href="#l3">     3</a></pre></td>
  <td><pre>line2
  <td class="followlines-btn-parent"><pre><a class="linenr" href="#l4">     4</a></pre></td>
  <td><pre>line3

  $ hgmo exec hgweb0 /var/hg/venv_hgweb/bin/hg --cwd /repo/hg/mozilla/mozilla-central --config fastannotate.modes=fastannotate fastannotate -r f01fe54ccaa1 foo
  0: line0
  1: line1 modified
  0: line2
  0: line3

  $ hgmo exec hgweb0 ls /repo/hg/mozilla/mozilla-central/.hg/fastannotate/default
  foo.l
  foo.m

  $ hgmo clean
