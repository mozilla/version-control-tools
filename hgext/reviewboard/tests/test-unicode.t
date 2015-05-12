#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ adminbugzilla create-user author@example.com password 'Patch Author'
  created user 6
  $ mozreview create-ldap-user author@example.com contributor 2001 'Some Contributor' --key-file ${MOZREVIEW_HOME}/keys/author@example.com --scm-level 1

Create a review request

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push > /dev/null
  $ rbmanage publish 1

Add a comment with unicode

  $ rbmanage create-review 1
  created review 1

The globbing is patching over a bug in mach
  $ rbmanage create-diff-comment 1 1 foo 1 'こんにちは世界'
  * UnicodeWarning: * (glob)
  * (glob)
  created diff comment 1
  $ rbmanage publish-review 1 1
  published review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc: []
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: Bug 1 - Initial commit to review
  
  
        Bug 1 - Initial commit to review'
    - author: author@example.com
      id: 3
      tags: []
      text: "http://*:$HGPORT1/r/1/#review1\n\n::: foo:1\n(Diff revision 1)\n\ (glob)
        > -foo\n> +initial\n\n\u3053\u3093\u306B\u3061\u306F\u4E16\u754C"
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Cleanup

  $ mozreview stop
  stopped 8 containers
