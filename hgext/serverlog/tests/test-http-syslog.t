#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser
  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

Mercurial wire protocol commands and HTTP commands logged to syslog

  $ hg clone ${HGWEB_0_URL}mozilla-central
  destination directory: mozilla-central
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ http --no-headers ${HGWEB_0_URL}mozilla-central > /dev/null
  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-repoinfo > /dev/null

  $ hgmo exec hgweb0 grep hgweb /var/log/hg.log
  * hgweb: * BEGIN_REQUEST mozilla-central * /mozilla-central?cmd=capabilities (glob)
  * hgweb: * BEGIN_PROTOCOL capabilities (glob)
  * hgweb: * END_REQUEST 0 * * (glob)
  * hgweb: * BEGIN_REQUEST mozilla-central * /mozilla-central?cmd=batch (glob)
  * hgweb: * BEGIN_PROTOCOL batch (glob)
  * hgweb: * END_REQUEST 0 * * (glob)
  * hgweb: * BEGIN_REQUEST mozilla-central * /mozilla-central?cmd=getbundle (glob)
  * hgweb: * BEGIN_PROTOCOL getbundle (glob)
  * hgweb: * END_REQUEST 82 * * (glob)
  * hgweb: * BEGIN_REQUEST mozilla-central * /mozilla-central (glob)
  * hgweb: * END_REQUEST 3858 * * (glob)
  * hgweb: * BEGIN_REQUEST mozilla-central * /mozilla-central/json-repoinfo (glob)
  * hgweb: * END_REQUEST 23 * * (glob)

  $ hgmo clean
