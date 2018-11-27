
Basic init

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > formatsource=$TESTDIR/hgext/format-source
  > rebase =
  > strip =
  > [format-source]
  > json = python $TESTDIR/hgext/format-source/tests/testlib/json-pretty.py
  > json:configpaths = .json-indent
  > json:fileext = .json
  > [default]
  > format-source=--date '0 0'
  > EOF
  $ HGMERGE=:merge3

  $ hg init test_repo
  $ cd test_repo

Commit various json file

  $ mkdir dir-1
  $ cat << EOF > dir-1/file-1.json
  > {"key1": [42,53,78], "key2": [9,3,8,1], "key3": ["London", "Paris", "Tokyo"]}
  > EOF
  $ cat << EOF > dir-1/file-2.json
  > {"key1": 1, "key2": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "key3": [54]}
  > EOF
  $ hg add .
  adding dir-1/file-1.json
  adding dir-1/file-2.json
  $ hg commit --message 'initial commit'

format them (in multiple steps)

  $ hg format-source --date '0 0' json glob:*/file-1.json -m 'format without config'
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID fb63bdd6edbf60d86f7aeaf0d806ecf6555c02eb
  # Parent  103bbf4a41e9e9010c27ab49c158f99b176d4f3e
  format without config
  
  diff -r 103bbf4a41e9 -r fb63bdd6edbf .hg-format-source
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/.hg-format-source	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +{"configpaths": [".json-indent"], "pattern": "glob:*/file-1.json", "tool": "json"}
  diff -r 103bbf4a41e9 -r fb63bdd6edbf dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,18 @@
  -{"key1": [42,53,78], "key2": [9,3,8,1], "key3": ["London", "Paris", "Tokyo"]}
  +{
  +    "key1": [
  +        42,
  +        53,
  +        78
  +    ],
  +    "key2": [
  +        9,
  +        3,
  +        8,
  +        1
  +    ],
  +    "key3": [
  +        "London",
  +        "Paris",
  +        "Tokyo"
  +    ]
  +}


  $ echo 2 > .json-indent
  $ hg add .json-indent
  $ python $TESTDIR/hgext/format-source/tests/testlib/json-pretty.py < dir-1/file-1.json > tmp
  $ mv tmp dir-1/file-1.json
  $ hg diff
  diff -r fb63bdd6edbf .json-indent
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/.json-indent	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +2
  diff -r fb63bdd6edbf dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,18 +1,18 @@
   {
  -    "key1": [
  -        42,
  -        53,
  -        78
  -    ],
  -    "key2": [
  -        9,
  -        3,
  -        8,
  -        1
  -    ],
  -    "key3": [
  -        "London",
  -        "Paris",
  -        "Tokyo"
  -    ]
  +  "key1": [
  +    42,
  +    53,
  +    78
  +  ],
  +  "key2": [
  +    9,
  +    3,
  +    8,
  +    1
  +  ],
  +  "key3": [
  +    "London",
  +    "Paris",
  +    "Tokyo"
  +  ]
   }
  $ hg commit -m 'reformat with indent=2'
  $ echo 1 > .json-indent
  $ python $TESTDIR/hgext/format-source/tests/testlib/json-pretty.py < dir-1/file-1.json > tmp
  $ mv tmp dir-1/file-1.json
  $ hg diff
  diff -r bacb7be97453 .json-indent
  --- a/.json-indent	Thu Jan 01 00:00:00 1970 +0000
  +++ b/.json-indent	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -2
  +1
  diff -r bacb7be97453 dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,18 +1,18 @@
   {
  -  "key1": [
  -    42,
  -    53,
  -    78
  -  ],
  -  "key2": [
  -    9,
  -    3,
  -    8,
  -    1
  -  ],
  -  "key3": [
  -    "London",
  -    "Paris",
  -    "Tokyo"
  -  ]
  + "key1": [
  +  42,
  +  53,
  +  78
  + ],
  + "key2": [
  +  9,
  +  3,
  +  8,
  +  1
  + ],
  + "key3": [
  +  "London",
  +  "Paris",
  +  "Tokyo"
  + ]
   }
  $ hg commit -m 'reformat with indent=1'

Add changes on another branch

  $ hg up 0
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ cat << EOF > dir-1/file-1.json
  > {"key1": [42,53,78,66], "key2": [9,3,8,1], "key3": ["London", "Paris", "Tokyo"]}
  > EOF
  $ cat << EOF > dir-1/file-2.json
  > {"key1": 1, "key2": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "key3": [54, 55]}
  > EOF
  $ hg commit -m 'some editions'
  created new head

Merge with "format without config"

  $ hg log -G
  @  changeset:   4:360af76de133
  |  tag:         tip
  |  parent:      0:103bbf4a41e9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     some editions
  |
  | o  changeset:   3:fa670ec0f89c
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     reformat with indent=1
  | |
  | o  changeset:   2:bacb7be97453
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     reformat with indent=2
  | |
  | o  changeset:   1:fb63bdd6edbf
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     format without config
  |
  o  changeset:   0:103bbf4a41e9
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial commit
  
  $ hg merge 1
  merging dir-1/file-1.json
  1 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg diff -r 'p2()' dir-1/file-1.json
  diff -r fb63bdd6edbf dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -2,7 +2,8 @@
       "key1": [
           42,
           53,
  -        78
  +        78,
  +        66
       ],
       "key2": [
           9,
  $ hg commit -m 'merge #1'

Merge with "format with indent=2"

  $ hg merge 2
  merging dir-1/file-1.json
  1 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg diff -r 'p2()' dir-1/file-1.json
  diff -r bacb7be97453 dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -2,7 +2,8 @@
     "key1": [
       42,
       53,
  -    78
  +    78,
  +    66
     ],
     "key2": [
       9,
  $ hg commit -m 'merge #2'

Merge with indent=1

  $ hg merge 3
  merging dir-1/file-1.json
  1 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg diff -r 'p2()' dir-1/file-1.json
  diff -r fa670ec0f89c dir-1/file-1.json
  --- a/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  +++ b/dir-1/file-1.json	Thu Jan 01 00:00:00 1970 +0000
  @@ -2,7 +2,8 @@
    "key1": [
     42,
     53,
  -  78
  +  78,
  +  66
    ],
    "key2": [
     9,
  $ hg commit -m 'merge #3'
