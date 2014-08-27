  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_string_changes = python:mozhghooks.prevent_string_changes.hook
  > EOF

Add file (tracked extension, outside expected path), should work

  $ hg init client
  $ cd client
  $ mkdir -p browser/locales/en-US
  $ echo "Configuration File" >> test.ini
  $ hg commit -A -m "Commit .ini file not relevant for l10n"
  adding test.ini
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Add file (untracked extension, outside expected path), should work

  $ echo "JavaScript file" >> test.js
  $ hg commit -A -m "Commit .js file outside l10n path"
  adding test.js
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Remove file (untracked extension, outside expected path), should work

  $ hg rm test.js
  $ hg commit -m "Remove .js file outside l10n path"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files

Add file (untracked extension, inside expected path), should work

  $ echo "Include file" >> browser/locales/en-US/test.inc
  $ hg commit -A -m "Commit .inc file inside l10n path"
  adding browser/locales/en-US/test.inc
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Remove file (untracked extension, inside expected path), should work

  $ hg rm browser/locales/en-US/test.inc
  $ hg commit -A -m "Remove .inc file inside l10n path"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files

Add file (tracked extension, inside expected path), wrong commit message, should fail

  $ mkdir -p browser/locales/en-US
  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ echo "DTD file #2" >> browser/locales/en-US/test2.dtd
  $ hg commit -A -m "Commit .dtd files inside l10n path, l10nok"
  adding browser/locales/en-US/test.dtd
  adding browser/locales/en-US/test2.dtd
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  * File used for localization (browser/locales/en-US/test2.dtd) altered in this changeset *
  
  This repository is string frozen. It is possible to override this
  block by adding a=l10n to the commit message.
  Before doing that, please CC a member of l10n-drivers to the bug
  to request approval and get feedback.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

Amend commit message to use correct keyword, should work

  $ hg commit --amend -m "Commit .dtd files inside l10n path, a=l10n"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/37c800ece1fa-amend-backup.hg
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  You've signaled approval for changes to strings in your push, thanks.

Edit existing file and commit with correct keyword, should work

  $ echo "Updated DTD content" >> browser/locales/en-US/test.dtd
  $ hg commit -A -m "Update .dtd file inside l10n path, a=l10n"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  You've signaled approval for changes to strings in your push, thanks.

Delete a file and commit without the correct keyword, should fail

  $ hg rm browser/locales/en-US/test.dtd
  $ hg commit -A -m "Remove .dtd file inside l10n path"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  
  This repository is string frozen. It is possible to override this
  block by adding a=l10n to the commit message.
  Before doing that, please CC a member of l10n-drivers to the bug
  to request approval and get feedback.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

  $ hg commit --amend -m "Remove .dtd file inside l10n path, a=l10n"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/aa1da582e4af-amend-backup.hg
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files
  You've signaled approval for changes to strings in your push, thanks.

Edit a file (tracked extension, inside expected path), as part of code uplift, should work

  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ hg commit -A -m 'Change DTD file on trunk, no need of approval'
  adding browser/locales/en-US/test.dtd
  $ echo "uplift1" > dummy
  $ hg commit -A -m 'Doing code upload; a=release'
  adding dummy
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files

Same edit of a tracked file after release uplift, should fail

  $ echo "uplift2" > dummy
  $ hg commit -m 'Doing the code uplift; a=release'
  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ hg commit -m 'Change DTD file'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  
  This repository is string frozen. It is possible to override this
  block by adding a=l10n to the commit message.
  Before doing that, please CC a member of l10n-drivers to the bug
  to request approval and get feedback.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

Message check should be case insensitive

  $ hg commit --amend -m "Remove .dtd file inside l10n path, A=L10N"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/19dffe1a0e53-amend-backup.hg
  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ hg commit -m 'Change DTD file, a=l10N'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 2 files
  You've signaled approval for changes to strings in your push, thanks.
