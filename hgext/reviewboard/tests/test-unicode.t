#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv rb-test-unicode

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ bugzilla create-user author@example.com password 'Patch Author'
  created user 5

Create a review request

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push http://localhost:$HGPORT/ > /dev/null
  $ rbmanage publish $HGPORT1 1

Add a comment with unicode

  $ rbmanage create-review $HGPORT1 1
  created review 1

The globbing is patching over a bug in mach
  $ rbmanage create-diff-comment $HGPORT1 1 1 foo 1 'こんにちは世界'
  * UnicodeWarning: * (glob)
  * (glob)
  created diff comment 1
  $ rbmanage publish-review $HGPORT1 1 1
  published review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://localhost:$HGPORT1/r/1/
      description: 'MozReview Request: bz://1/mynick'
      file_name: reviewboard-1-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: bz://1/mynick'
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
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Initial commit to review
  
  
        Pull down this commit:
  
  
        hg pull -r 57755461e85f1e3e66738ec2d57f325249897409 http://localhost:$HGPORT/'
    - author: author@example.com
      id: 3
      tags: []
      text: "http://localhost:$HGPORT1/r/1/#review1\n\n::: foo\n(Diff revision 1)\n> -foo\n\
        > +initial\n\n\u3053\u3093\u306B\u3061\u306F\u4E16\u754C"
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Cleanup

  $ rbmanage stop rbserver
  $ dockercontrol stop-bmo rb-test-unicode
  stopped 3 containers
