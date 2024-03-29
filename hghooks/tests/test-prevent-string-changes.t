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

Add DTD files (tracked extension, inside expected path), wrong commit message, should fail

  $ mkdir -p browser/locales/en-US
  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ echo "DTD file #2" >> browser/locales/en-US/test2.dtd
  $ hg commit -A -m "Commit .dtd files inside l10n path, a=l10n"
  adding browser/locales/en-US/test.dtd
  adding browser/locales/en-US/test2.dtd
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files (no-hg59 !)
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  * File used for localization (browser/locales/en-US/test2.dtd) altered in this changeset *
  
  This repository is string frozen. Please request explicit permission from
  release managers to break string freeze in your bug.
  If you have that explicit permission, denote that by including in
  your commit message l10n=...
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

Amend commit message to use correct keyword, should work

  $ hg -q commit --amend -m "Commit .dtd files inside l10n path, l10n=foo"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks. (hg59 !)
  added 1 changesets with 2 changes to 2 files
  You've signaled approval for changes to strings in your push, thanks. (no-hg59 !)

Add Fluent file (tracked extension, inside expected path), wrong commit message, should fail

  $ mkdir -p browser/locales/en-US
  $ echo "FTL file" >> browser/locales/en-US/test.ftl
  $ hg commit -A -m "Commit .ftl files inside l10n path, a=l10n"
  adding browser/locales/en-US/test.ftl
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files (no-hg59 !)
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.ftl) altered in this changeset *
  
  This repository is string frozen. Please request explicit permission from
  release managers to break string freeze in your bug.
  If you have that explicit permission, denote that by including in
  your commit message l10n=...
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

Amend commit message to use correct keyword, should work

  $ hg -q commit --amend -m "Commit .ftl files inside l10n path, l10n=foo"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks. (hg59 !)
  added 1 changesets with 1 changes to 1 files
  You've signaled approval for changes to strings in your push, thanks. (no-hg59 !)

Edit existing file and commit with correct keyword, should work

  $ echo "Updated DTD content" >> browser/locales/en-US/test.dtd
  $ hg commit -A -m "Update .dtd file inside l10n path, l10n=foo"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks. (hg59 !)
  added 1 changesets with 1 changes to 1 files
  You've signaled approval for changes to strings in your push, thanks. (no-hg59 !)

Delete a file and commit without the correct keyword, should fail

  $ hg rm browser/locales/en-US/test.dtd
  $ hg commit -A -m "Remove .dtd file inside l10n path"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  
  This repository is string frozen. Please request explicit permission from
  release managers to break string freeze in your bug.
  If you have that explicit permission, denote that by including in
  your commit message l10n=...
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

  $ hg -q commit --amend -m "Remove .dtd file inside l10n path, l10n=foo"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks. (hg59 !)
  added 1 changesets with 0 changes to 0 files
  You've signaled approval for changes to strings in your push, thanks. (no-hg59 !)

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
  added 2 changesets with 2 changes to 2 files (no-hg59 !)
  
  ************************** ERROR ****************************
  
  * File used for localization (browser/locales/en-US/test.dtd) altered in this changeset *
  
  This repository is string frozen. Please request explicit permission from
  release managers to break string freeze in your bug.
  If you have that explicit permission, denote that by including in
  your commit message l10n=...
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_string_changes hook failed
  [255]

Message check should be case insensitive

  $ hg -q commit --amend -m "Remove .dtd file inside l10n path, L10n=foo"
  $ echo "DTD file #1" >> browser/locales/en-US/test.dtd
  $ hg commit -m 'Change DTD file, l10N='
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks. (hg59 !)
  added 3 changesets with 3 changes to 2 files
  You've signaled approval for changes to strings in your push, thanks. (no-hg59 !)

Hook lets approval for non-tip commits pass

  $ echo "DTD file in uplift3" >> browser/locales/en-US/test.dtd
  $ hg commit -m 'Change DTD file for uplift3. l10n='
  $ echo "uplift4" > dummy
  $ hg commit -m 'Doing uplift4 without localization change and approval'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  You've signaled approval for changes to strings in your push, thanks.
  added 2 changesets with 2 changes to 2 files

  $ cd ..

Hook should not run when stripping

  $ hg init striptest
  $ cd striptest
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ echo good > foo
  $ hg commit -m 'Good commit'
  $ hg -q up -r 0
  $ mkdir -p browser/locales/en-US
  $ echo 'DTD file #1' > browser/locales/en-US/test.dtd
  $ hg -q commit -A -m 'Bad commit'

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip =
  > 
  > [hooks]
  > pretxnchangegroup.prevent_string_changes = python:mozhghooks.prevent_string_changes.hook
  > EOF

  $ hg strip -r 1 --no-backup

  $ hg log -T '{rev} {desc}\n'
  1 Bad commit
  0 initial
