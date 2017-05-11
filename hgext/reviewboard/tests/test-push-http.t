#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Seed repository on server

  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -r .
  $ hg push --noreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

A HTTP GET request should not require authentication

  $ http ${MERCURIAL_URL}test-repo/json-pushes
  200
  connection: close
  content-type: application/json
  date: * (glob)
  etag: * (glob)
  server: Apache
  strict-transport-security: max-age=300
  transfer-encoding: chunked
  
  {"1": {"changesets": ["96ee1d7354c4ad7372047672c36a1f561e3a6a4c"], "date": *, "user": "default@example.com"}} (glob)

Capabilities are exposed via JSON API

  $ http --no-headers ${MERCURIAL_URL}test-repo/json-mozreviewcapabilities
  200
  
  {
    "reviewcaps": [
      "publish", 
      "publishhttp", 
      "pullreviews", 
      "pushreview", 
      "submithttp"
    ], 
    "reviewrequires": [
      "bzapikeys", 
      "commitid", 
      "jsonproto", 
      "listreviewdata", 
      "listreviewrepos", 
      "proto1"
    ]
  }

hg pull does not require authentication

  $ hg --config extensions.strip= strip -r tip
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/96ee1d7354c4-05cd9e87-backup.hg (glob)

  $ hg pull ${MERCURIAL_URL}test-repo
  pulling from http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg up -r tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Issuing a POST to the Mercurial server requires authentication

  $ http --method POST --request-header 'Content-Type: text/plain' ${MERCURIAL_URL}test-repo/json-pushes
  401
  connection: close
  content-length: 381
  content-type: text/html; charset=iso-8859-1
  date: * (glob)
  server: Apache
  www-authenticate: Basic realm="http://$DOCKER_HOSTNAME:$HGPORT2/ username and API Key"
  
  <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
  <html><head>
  <title>401 Unauthorized</title>
  </head><body>
  <h1>Unauthorized</h1>
  <p>This server could not verify that you
  are authorized to access the document
  requested.  Either you supplied the wrong
  credentials (e.g., bad password), or your
  browser doesn't understand how to supply
  the credentials required.</p>
  </body></html>
  

Invalid credentials should result in 401

  $ http --method POST --request-header 'Content-Type: text/plain' --basic-username default@example.com --basic-password invalid ${MERCURIAL_URL}test-repo/json-pushes
  401
  connection: close
  content-length: 381
  content-type: text/html; charset=iso-8859-1
  date: * (glob)
  server: Apache
  www-authenticate: Basic realm="http://$DOCKER_HOSTNAME:$HGPORT2/ username and API Key"
  
  <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
  <html><head>
  <title>401 Unauthorized</title>
  </head><body>
  <h1>Unauthorized</h1>
  <p>This server could not verify that you
  are authorized to access the document
  requested.  Either you supplied the wrong
  credentials (e.g., bad password), or your
  browser doesn't understand how to supply
  the credentials required.</p>
  </body></html>
  

Valid API key with wrong username should result in 401

  $ defaultkey=`mozreview create-api-key default@example.com`
  $ http --method POST --request-header 'Content-Type: text/plain' --basic-username invalid@example.com --basic-password ${defaultkey} ${MERCURIAL_URL}test-repo/json-pushes
  401
  connection: close
  content-length: 381
  content-type: text/html; charset=iso-8859-1
  date: * (glob)
  server: Apache
  www-authenticate: Basic realm="http://$DOCKER_HOSTNAME:$HGPORT2/ username and API Key"
  
  <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
  <html><head>
  <title>401 Unauthorized</title>
  </head><body>
  <h1>Unauthorized</h1>
  <p>This server could not verify that you
  are authorized to access the document
  requested.  Either you supplied the wrong
  credentials (e.g., bad password), or your
  browser doesn't understand how to supply
  the credentials required.</p>
  </body></html>
  

Valid user and API key is authenticated properly

  $ http --method POST --request-header 'Content-Type: text/plain' --basic-username default@example.com --basic-password ${defaultkey} --request-header "Content-Type: text/plain" ${MERCURIAL_URL}test-repo/json-pushes
  200
  connection: close
  content-type: application/json
  date: * (glob)
  etag: * (glob)
  server: Apache
  strict-transport-security: max-age=300
  transfer-encoding: chunked
  
  {"1": {"changesets": ["96ee1d7354c4ad7372047672c36a1f561e3a6a4c"], "date": *, "user": "default@example.com"}} (glob)

Vanilla push over HTTP should require authorization

  $ echo http1 > foo
  $ hg commit -m 'non review push over http'
  $ hg push ${MERCURIAL_URL}test-repo
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/1b5eacce6121-7f714e89-addcommitid.hg (glob)
  searching for changes
  abort: http authorization required for http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  [255]

Vanilla push will prompt for credentials

  $ hg --config ui.interactive=true push ${MERCURIAL_URL}test-repo
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  searching for changes
  http authorization required for http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  realm: http://$DOCKER_HOSTNAME:$HGPORT2/ username and API Key
  user: abort: response expected
  [255]

Credentials are automagically found if [bugzilla] configs are defined

  $ hg -q up -r 0
  $ echo autocreds > foo
  $ hg commit -m 'auto find bugzilla credentials'
  created new head
  $ hg --config mozilla.trustedbmoapikeyservices=${MERCURIAL_URL} push ${MERCURIAL_URL}test-repo --noreview -r .
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ hg -q up -r 1

Vanilla push with invalid credentials fails

  $ cat >> .hg/hgrc << EOF
  > [auth]
  > t.prefix = ${MERCURIAL_URL}
  > t.username = default@example.com
  > t.password = invalid
  > EOF

  $ hg push ${MERCURIAL_URL}test-repo
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  searching for changes
  abort: authorization failed
  [255]

Vanilla push with proper credentials works

  $ cat >> .hg/hgrc << EOF
  > t.password = ${defaultkey}
  > EOF

  $ hg push ${MERCURIAL_URL}test-repo --noreview -r .
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog

The Bugzilla user should have been recorded in the pushlog

  $ http ${MERCURIAL_URL}test-repo/json-pushes --no-headers --body-file body
  200

  $ python -m json.tool < body
  {
      "1": {
          "changesets": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "date": *, (glob)
          "user": "default@example.com"
      },
      "2": {
          "changesets": [
              "12ee4d2b76f57e27a8bcacd2063487a6bde7d7fd"
          ],
          "date": *, (glob)
          "user": "bmo:default@example.com"
      },
      "3": {
          "changesets": [
              "6ab4007f52489a76cbff3f80e3d7baa5d99fbb3c"
          ],
          "date": *, (glob)
          "user": "bmo:default@example.com"
      }
  }

Test with a second user, just so we are comprehensive

  $ mozreview create-user user2@example.com password 'User Two [:user2]' --bugzilla-group editbugs
  Created user 6
  $ user2key=`mozreview create-api-key user2@example.com`

  $ echo user2 > foo
  $ hg commit -m 'push from user2'
  $ hg phase --public -r .

  $ cat >> .hg/hgrc << EOF
  > t.username = user2@example.com
  > t.password = ${user2key}
  > EOF

  $ hg push --noreview ${MERCURIAL_URL}test-repo -r .
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ http ${MERCURIAL_URL}test-repo/json-pushes --no-headers --body-file body
  200

  $ python -m json.tool < body
  {
      "1": {
          "changesets": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "date": *, (glob)
          "user": "default@example.com"
      },
      "2": {
          "changesets": [
              "12ee4d2b76f57e27a8bcacd2063487a6bde7d7fd"
          ],
          "date": *, (glob)
          "user": "bmo:default@example.com"
      },
      "3": {
          "changesets": [
              "6ab4007f52489a76cbff3f80e3d7baa5d99fbb3c"
          ],
          "date": *, (glob)
          "user": "bmo:default@example.com"
      },
      "4": {
          "changesets": [
              "8d7f5c4152d8f67d67500d3b92903e365c0122f1"
          ],
          "date": *, (glob)
          "user": "bmo:user2@example.com"
      }
  }

Test creating a review via HTTP

  $ echo review1 > foo
  $ hg commit -m 'Bug 1 - Review 1; r?reviewer'
  $ echo review2 > foo
  $ hg commit -m 'Bug 1 - Review 2; r?reviewer'

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ mozreview create-user reviewer@example.com password 'Reviewer :reviewer'
  Created user 7

  $ hg --config bugzilla.username=user2@example.com --config bugzilla.apikey=${user2key} push ${MERCURIAL_URL}test-repo
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/e528ead97c56-8d25fba9-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  4:9d326020e0dc
  summary:    Bug 1 - Review 1; r?reviewer
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  5:c6548fe14585
  summary:    Bug 1 - Review 2; r?reviewer
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: user2
  summary: bz://1/mynick
  description: This is the parent review request
  target_people:
  - reviewer
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 8d7f5c4152d8f67d67500d3b92903e365c0122f1
    p2rb.commits: '[["9d326020e0dcd3e421680e4b78bf80c9e30df0e6", 2], ["c6548fe145857055779b23d94ef3f911e8d261b0",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.first_public_ancestor: 8d7f5c4152d8f67d67500d3b92903e365c0122f1
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 8d7f5c4152d8f67d67500d3b92903e365c0122f1
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -user2
    - +review2
    - ''
  approved: false
  approval_failure: Commit 9d326020e0dcd3e421680e4b78bf80c9e30df0e6 is not approved.

  $ rbmanage dump-user user2
  4:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    id: 4
    url: /users/user2/
    username: user2

No LDAP user should be associated with user2 since push arrived via HTTP
and no LDAP username was available.
(This may fail in the future because we used `mozreview create-user` above,
which actually does create an LDAP user: we're just not using it here.)

  $ rbmanage dump-user-ldap user2
  no ldap username associated with user2

Cleanup

  $ mozreview stop
  stopped 9 containers
