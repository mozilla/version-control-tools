#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central 1
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
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 3 changes to 3 files
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in \d+\.\d+s (re)
  remote: replication of changegroup data completed successfully in \d+\.\d+s (re)
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be
  remote:   https://hg.mozilla.org/mozilla-central/rev/eefea2647aef

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/file/eefea2647aef/foo.js | grep linenr
  <pre><a class="linenr" href="#l1" id="l1">     1</a> <span class="kd">var</span> <span class="nx">foo</span> <span class="o">=</span> <span class="s2">&quot;bar&quot;</span><span class="p">;</span></pre>
  <pre><a class="linenr" href="#l2" id="l2">     2</a> <span class="kd">function</span> <span class="nx">sum</span><span class="p">(</span><span class="nx">a</span><span class="p">,</span> <span class="nx">b</span><span class="p">)</span> <span class="p">{</span></pre>
  <pre><a class="linenr" href="#l3" id="l3">     3</a>   <span class="k">return</span> <span class="nx">a</span> <span class="o">+</span> <span class="nx">b</span><span class="p">;</span></pre>
  <pre><a class="linenr" href="#l4" id="l4">     4</a> <span class="p">}</span></pre>

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/file/eefea2647aef/foo.jsm | grep linenr
  <pre><a class="linenr" href="#l1" id="l1">     1</a> <span class="kd">var</span> <span class="nx">foo</span> <span class="o">=</span> <span class="s2">&quot;bar&quot;</span><span class="p">;</span></pre>
  <pre><a class="linenr" href="#l2" id="l2">     2</a> <span class="kd">function</span> <span class="nx">sum</span><span class="p">(</span><span class="nx">a</span><span class="p">,</span> <span class="nx">b</span><span class="p">)</span> <span class="p">{</span></pre>
  <pre><a class="linenr" href="#l3" id="l3">     3</a>   <span class="k">return</span> <span class="nx">a</span> <span class="o">+</span> <span class="nx">b</span><span class="p">;</span></pre>
  <pre><a class="linenr" href="#l4" id="l4">     4</a> <span class="p">}</span></pre>

Cleanup

  $ hgmo clean
