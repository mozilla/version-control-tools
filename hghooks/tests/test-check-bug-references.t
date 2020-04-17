  $ . $TESTDIR/hghooks/tests/common.sh

Setup the try repo and add a single file after enabling the check in hgrc.
  $ hg init try
  $ configurehooks try 
  $ sed -i '/^\[mozilla\]$/a check_bug_references_repos = try' try/.hg/hgrc
  $ cd try
  $ touch hello
  $ hg -q commit -A -m 'first commit'
  $ cd ..

Clone the try repo to a client directory and add a new file
  $ hg clone try client
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ touch client/file

  $ cat >> client/.hg/hgrc << EOF
  > [extensions]
  > advancedurlintercept = $TESTDIR/testing/advanced_url_intercept.py
  > 
  > [advancedurlintercept]
  > path = $TESTTMP/url
  > EOF


  $ cat > $TESTTMP/url << EOF
  > {
  >   "https://bugzilla.mozilla.org/rest/bug?id=1000000&include_fields=id": {
  >     "code": null
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=2000000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": [
  >         {
  >           "id": "2000000"
  >         }
  >       ]
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=4000000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": []
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=4010000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": []
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=2000000%2C4010000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": [
  >         {
  >           "id": "2000000"
  >         }
  >       ]
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=4040000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": []
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug?id=5000000&include_fields=id": {
  >     "code": 200,
  >     "data": {
  >       "bugs": []
  >     }
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/1000000": {
  >     "code": null
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/2000000": {
  >     "code": 200,
  >     "data": {}
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/4000000": {
  >     "code": 400
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/4010000": {
  >     "code": 401
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/4040000": {
  >     "code": 404
  >   },
  >   "https://bugzilla.mozilla.org/rest/bug/5000000": {
  >     "code": 500
  >   }
  > }
  > EOF


Run various commit and push commands to test for the correct behaviour

Test that the hook rejects commits when Bugzilla can not be accessed.
  $ cd client
  $ hg commit -A -m "fix for bug 1000000"
  adding file
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (no-hg52 !)
  
  ********************************* ERROR **********************************
  Could not access bugzilla.mozilla.org to check if a bug referenced in your
  commit message is a security bug. Please try again later.
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  **************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test that the hook reject commits when bug IDs could not be verified.
  $ hg commit --amend -m "fix for bug 4000000"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/d9b5eab34108-6d0f6138-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************************************ ERROR ************************************
  While checking if a bug referenced in your commit message is a security bug, an
  error occurred and the bug could not be verified.
  
      Affected bug: 4000000
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  *******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test that the hook rejects references to bugs that do not have public permissions.
  $ hg commit --amend -m "fix for bug 4010000"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/2d526a6f125f-1fd0f982-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************************************ ERROR ************************************
  Your commit message references bugs that are currently private. To avoid
  disclosing the nature of these bugs publicly, please remove the affected bug ID
  from the commit message.
  
      Affected bug: 4010000
  
  Visit https://wiki.mozilla.org/Security/Bug_Approval_Process for more
  information.
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  *******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

  $ hg commit --amend -m "fix for bug 4010000 and bug 2000000"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/99f50ae1c4b1-f2a0e514-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************************************ ERROR ************************************
  Your commit message references bugs that are currently private. To avoid
  disclosing the nature of these bugs publicly, please remove the affected bug ID
  from the commit message.
  
      Affected bug: 4010000
  
  Visit https://wiki.mozilla.org/Security/Bug_Approval_Process for more
  information.
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  *******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test that the hook rejects references to bugs that do not exist.
  $ hg commit --amend -m "fix for bug 4040000"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/7540d6240847-18b7d292-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************************** ERROR **********************************
  Your commit message references a bug that does not exist. Please check your
  commit message and try again.
  
      Affected bug: 4040000
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  ***************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test that the hook rejects commits when BMO returns a server error.
  $ hg commit --amend -m "fix for bug 5000000"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/7585222b7453-339468ad-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************************************ ERROR ************************************
  While checking if a bug referenced in your commit message is a security bug, an
  error occurred and the bug could not be verified.
  
      Affected bug: 5000000
  
  
  To push this commit anyway and ignore this warning, include SKIP_BMO_CHECK
  in your commit message.
  *******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test that the hook allows push when override flag is included in commit message.
  $ hg commit --amend -m "fix for bug 4010000 and bug 2000000 SKIP_BMO_CHECK"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/02da675da158-6366be00-amend.hg
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************************** WARNING **********************************
  You have chosen to ignore or skip checking bugs IDs referenced in your commit
  message. Security bugs or invalid bugs referenced will not block your push.
  *****************************************************************************
  
  added 1 changesets with 1 changes to 1 files

Test that the hook does not reject commits that have a valid bug ID.
  $ touch some_other_file
  $ hg commit -A -m "fix for bug 2000000"
  adding some_other_file
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Test that the hook does not reject public commits.
  $ touch another_file
  $ hg commit -A -m "fix for bug 4010000"
  adding another_file
  $ hg phase -v  --public
  phase changed for 1 changesets
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Test disabling the hook via hgrc config (i.e. no checks/warnings should occur)
  $ sed -i 's/check_bug_references_repos = try//g' ../try/.hg/hgrc
  $ touch yet_another_file
  $ hg commit -A -m "fix for bug 4010000"
  adding yet_another_file
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
