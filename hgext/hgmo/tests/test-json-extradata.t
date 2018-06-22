  $ export USER=hguser
  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

Install a custom commit command to simulate extra changeset data getting added by an extension.

  $ cat > $TESTTMP/commitextradata.py <<EOF
  > def reposetup(ui, repo):
  >     class extrarepo(repo.__class__):
  >         def commit(self, *args, **kwargs):
  >             extra = kwargs.setdefault('extra', {})
  >             extra['moz-landing-system'] = 'wobble'
  >             return super(extrarepo, self).commit(*args, **kwargs)
  > 
  >     repo.__class__ = extrarepo
  > EOF

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > commitextradata = $TESTTMP/commitextradata.py
  > EOF

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 271; r=calixte'
  $ hg -q push
  $ echo second > foo
  $ cat > message << EOF
  > Bug 828 - Do foo; r=calixte
  > 
  > This is related to bug 182.
  > EOF
  $ hg commit -l message
  $ hg -q push

  $ echo third > foo
  $ hg commit -m 'NO BUG'

  $ hg -q push

Check the last changeset

  $ http http://localhost:$HGPORT/json-rev/tip --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "backedoutby": "",
      "bookmarks": [],
      "branch": "default",
      "date": [
          0.0,
          0
      ],
      "desc": "NO BUG",
      "landingsystem": "wobble",
      "node": "40e31a84e3dcf059c2e33d5a266edc6bad3b81ed",
      "parents": [
          "afa8227ab48e5f3c749fb59f2e886cb487594cf2"
      ],
      "phase": "public",
      "pushdate": [
          \d+, (re)
          \d+ (re)
      ],
      "pushid": 3,
      "pushuser": "hguser",
      "tags": [
          "tip"
      ],
      "user": "test"
  }

Confirm no errors in log

  $ cat ../server/error.log
