  $ export HGUSER='Valid User <someone@example.com>'
  $ hg init server
  $ cat > server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.author_format = python:mozhghooks.author_format.hook
  > EOF

  $ hg -q clone --pull server client
  $ cd client

Well formed user is allowed

  $ touch foo
  $ hg -q commit -A -u 'Valid User <someone@example.com>' -m valid
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Just a user name with no email is rejected

  $ echo invalid > foo
  $ hg commit -u 'Just Username' -m invalid
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset d28cf3d35b22: Just Username
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r d28cf3d35b22::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r d28cf3d35b22::d28cf3d35b22`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Just an email address is rejected

  $ hg commit --amend -u 'someone@example.com' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/d28cf3d35b22-3e561411-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset 7912d5cf9855: someone@example.com
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r 7912d5cf9855::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r 7912d5cf9855::7912d5cf9855`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Just an email address in brackets is rejected

  $ hg commit --amend -u '<someone@example.com>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/7912d5cf9855-ac6aad27-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset 171604c7eccc: <someone@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r 171604c7eccc::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r 171604c7eccc::171604c7eccc`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

No space between author and email is rejected

  $ hg commit --amend -u 'No Space<someone@example.com>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/171604c7eccc-0285e4c9-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset c7bd56f10523: No Space<someone@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r c7bd56f10523::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r c7bd56f10523::c7bd56f10523`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Multiple angle brackets are rejected

  $ hg commit --amend -u 'Multiple LessThan <<someone@example.com>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/c7bd56f10523-a3c3737b-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset 3ff22b11fa53: Multiple LessThan <<someone@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r 3ff22b11fa53::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r 3ff22b11fa53::3ff22b11fa53`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

  $ hg commit --amend -u 'Multiple GreaterTHan <someone@example.com>>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/3ff22b11fa53-a2861ff2-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset 57a242fa12b7: Multiple GreaterTHan <someone@example.com>>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r 57a242fa12b7::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r 57a242fa12b7::57a242fa12b7`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

More complicated strings are rejected

  $ hg commit --amend -u 'First Author <someone1@example.com>, Second Author <someone@example.com>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/57a242fa12b7-1da20aa0-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset ee5f32d2fdc3: First Author <someone1@example.com>, Second Author <someone@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r ee5f32d2fdc3::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r ee5f32d2fdc3::ee5f32d2fdc3`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

  $ hg commit --amend -u 'First Author <someone1@example.com> with tweaks by Second Author <someone2@example.com>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/ee5f32d2fdc3-17e4c454-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset ccd3d34a2a22: First Author <someone1@example.com> with tweaks by Second Author <someone2@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r ccd3d34a2a22::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r ccd3d34a2a22::ccd3d34a2a22`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Emails without @<domain> are rejected

  $ hg commit --amend -u 'Valid Author <someone>' -m invalid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/ccd3d34a2a22-590fe923-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  malformed user field in changeset 514432ecc4d9: Valid Author <someone>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r 514432ecc4d9::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r 514432ecc4d9::514432ecc4d9`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Multiple changesets are listed in error message

  $ hg commit --amend -u 'Valid User <valid@example.com>' -m valid
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/514432ecc4d9-4a80f047-amend*.hg (glob)
  $ echo invalid1 > foo
  $ hg commit -u 'Invalid' -m invalid1
  $ echo invalid2 > foo
  $ hg commit -u '<invalid2@example.com>' -m invalid2
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  malformed user field in changeset e9718df8a2f3: Invalid
  malformed user field in changeset f088c66168eb: <invalid2@example.com>
  user fields must be of the format "author <email>"
  e.g. "Mozilla Contributor <someone@example.com>"
  set "ui.username" in your hgrc to a well-formed value
  
  "graft" can be used to rewrite multiple changesets to have a different user value
  use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user
  
  `hg up b393ea5c71c2 && hg graft --currentuser -r c46d23f5af6e::`
  will rewrite all pushed changesets and their descendants to the current user value
  
  `hg up b393ea5c71c2 && hg graft --user 'Some User <someone@example.com>' -r c46d23f5af6e::f088c66168eb`
  will rewrite just the pushed changesets to an explicit username
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.author_format hook failed
  [255]

Make sure the suggested instructions work

  $ hg up b393ea5c71c2 && hg graft --currentuser -r c46d23f5af6e::
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  grafting 1:c46d23f5af6e "valid"
  grafting 2:e9718df8a2f3 "invalid1"
  grafting 3:f088c66168eb "invalid2" (tip)
  $ hg push -r .
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
