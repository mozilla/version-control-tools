#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:$HGPORT/mozilla-central
  $ cd mozilla-central

Create a repository

  $ touch foo
  $ hg -q commit -A -m initial

  $ cat > foo.js << EOF
  > var foo = "bar";
  > function sum(a, b) {
  >   return a + b;
  > }
  > EOF

  $ cp foo.js foo.jsm
  $ hg -q commit -A -m js-files

  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 3 changes to 3 files
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote:   https://hg.mozilla.org/mozilla-central/rev/eefea2647aef3c12004101eccb526a485b0144a4
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/file/eefea2647aef/foo.js | grep 'href="#l'
  <a href="#l1"></a><span id="l1"><span class="kd">var</span> <span class="nx">foo</span> <span class="o">=</span> <span class="s2">&quot;bar&quot;</span><span class="p">;</span></span>
  <a href="#l2"></a><span id="l2"><span class="kd">function</span> <span class="nx">sum</span><span class="p">(</span><span class="nx">a</span><span class="p">,</span> <span class="nx">b</span><span class="p">)</span> <span class="p">{</span></span>
  <a href="#l3"></a><span id="l3">  <span class="k">return</span> <span class="nx">a</span> <span class="o">+</span> <span class="nx">b</span><span class="p">;</span></span>
  <a href="#l4"></a><span id="l4"><span class="p">}</span></span>

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/file/eefea2647aef/foo.jsm | grep 'href="#l'
  <a href="#l1"></a><span id="l1"><span class="kd">var</span> <span class="nx">foo</span> <span class="o">=</span> <span class="s2">&quot;bar&quot;</span><span class="p">;</span></span>
  <a href="#l2"></a><span id="l2"><span class="kd">function</span> <span class="nx">sum</span><span class="p">(</span><span class="nx">a</span><span class="p">,</span> <span class="nx">b</span><span class="p">)</span> <span class="p">{</span></span>
  <a href="#l3"></a><span id="l3">  <span class="k">return</span> <span class="nx">a</span> <span class="o">+</span> <span class="nx">b</span><span class="p">;</span></span>
  <a href="#l4"></a><span id="l4"><span class="p">}</span></span>

Cleanup

  $ hgmo clean
