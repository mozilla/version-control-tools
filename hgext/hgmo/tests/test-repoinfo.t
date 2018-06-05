  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ http "http://localhost:$HGPORT/json-repoinfo" --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "group_owner": "*" (glob)
  }

  $ http "http://localhost:$HGPORT/repoinfo" --header content-type --body-file body
  200
  content-type: text/html; charset=ascii

  $ grep Push body
    <tr><td>Push Group</td><td>*</td></tr> (glob)
