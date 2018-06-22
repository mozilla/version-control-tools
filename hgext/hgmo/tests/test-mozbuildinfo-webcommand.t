TODO bug 1224320 moz.build doesn't work with code coverage enabled.
Ensure code coverage isn't enabled
  $ unset CODE_COVERAGE

  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ cat > moz.build << EOF
  > with Files('**'):
  >     BUG_COMPONENT = ('Product1', 'Component 1')
  > EOF

  $ hg -q commit -A -m 'associate with product1'

  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  remote: recorded push in pushlog

  $ cd ..

Web command isn't available unless enabled

  $ http http://localhost:$HGPORT/json-mozbuildinfo/72cb73cd1ba4 --header content-type
  200
  content-type: application/json
  
  {"error": "moz.build evaluation is not enabled for this repo"}

Confirm no errors in log

  $ cat ./server/error.log

Restart server with evaluation enabled

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hgmo]
  > mozbuildinfoenabled = True
  > EOF

  $ hg serve -d -p $HGPORT1 --pid-file hg.pid -E error2.log --hgmo
  listening at http://localhost:$HGPORT1/ (bound to $LOCALIP:$HGPORT1) (?)
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Web command errors unless a wrapper is defined

  $ http http://localhost:$HGPORT1/json-mozbuildinfo/72cb73cd1ba4 --header content-type
  200
  content-type: application/json
  
  {"error": "moz.build wrapper command not defined; refusing to execute"}

Confirm no errors in log

  $ cat ./server/error2.log

Restart the server with dummy wrapper

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hgmo]
  > mozbuildinfowrapper = `which hg` --config extensions.hgmo=$TESTDIR/hgext/hgmo mozbuildinfo --pipemode
  > EOF

  $ hg serve -d -p $HGPORT2 --pid-file hg.pid -E error3.log --hgmo
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

mozbuildinfo is available via web command
(this also tests that no file argument uses files from commit)

  $ http http://localhost:$HGPORT2/json-mozbuildinfo/72cb73cd1ba4 --header content-type
  200
  content-type: application/json
  
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product1",
            "Component 1"
          ],
          1
        ]
      ],
      "recommended_bug_component": [
        "Product1",
        "Component 1"
      ]
    },
    "files": {
      "moz.build": {
        "bug_component": [
          "Product1",
          "Component 1"
        ]
      }
    }
  }

we can request info for specific files

  $ http "http://localhost:$HGPORT2/json-mozbuildinfo/72cb73cd1ba4?p=file1&p=file2" --header content-type
  200
  content-type: application/json
  
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product1",
            "Component 1"
          ],
          2
        ]
      ],
      "recommended_bug_component": [
        "Product1",
        "Component 1"
      ]
    },
    "files": {
      "file1": {
        "bug_component": [
          "Product1",
          "Component 1"
        ]
      },
      "file2": {
        "bug_component": [
          "Product1",
          "Component 1"
        ]
      }
    }
  }

Errors displayed properly

  $ http http://localhost:$HGPORT2/json-mozbuildinfo/55482a6fb4b1 --header content-type
  200
  content-type: application/json
  
  {
    "error": "no moz.build info available"
  }

Confirm no errors in log

  $ cat ./server/error3.log

Restart the server with a bad wrapper command

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hgmo]
  > mozbuildinfowrapper = /does/not/exist
  > EOF
  $ hg serve -d -p $HGPORT3 --pid-file hg.pid -E error4.log --hgmo
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ http http://localhost:$HGPORT3/json-mozbuildinfo/72cb73cd1ba4 --header content-type
  200
  content-type: application/json
  
  {"error": "unable to invoke moz.build info process"}

Confirm no errors in log

  $ cat ./server/error4.log

Restart the server with a wrapper that doesn't emit JSON

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hgmo]
  > mozbuildinfowrapper = $TESTDIR/hgext/hgmo/tests/wrapper-not-json
  > EOF
  $ hg serve -d -p $HGPORT4 --pid-file hg.pid --hgmo -E error5.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ http http://localhost:$HGPORT4/json-mozbuildinfo/72cb73cd1ba4 --header content-type
  200
  content-type: application/json
  
  {"error": "invalid JSON returned; report this error"}


Confirm no errors in log

  $ cat ./server/error5.log
