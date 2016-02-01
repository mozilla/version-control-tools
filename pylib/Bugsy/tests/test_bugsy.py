from . import rest_url
from bugsy import (Bugsy, Bug)
from bugsy.errors import (BugsyException, LoginException)

import responses
import json

example_return = {u'faults': [], u'bugs': [{u'cf_tracking_firefox29': u'---', u'classification': u'Other', u'creator': u'jgriffin@mozilla.com', u'cf_status_firefox30':
u'---', u'depends_on': [], u'cf_status_firefox32': u'---', u'creation_time': u'2014-05-28T23:57:58Z', u'product': u'Release Engineering', u'cf_user_story': u'', u'dupe_of': None, u'cf_tracking_firefox_relnote': u'---', u'keywords': [], u'cf_tracking_b2g18': u'---', u'summary': u'Schedule Mn tests on o\
pt Linux builds on cedar', u'id': 1017315, u'assigned_to_detail': {u'id': 347295, u'email': u'jgriffin@mozilla.com', u'name': u'jgriffin@mozilla.com',
u'real_name': u'Jonathan Griffin (:jgriffin)'}, u'severity': u'normal', u'is_confirmed': True, u'is_creator_accessible': True, u'cf_status_b2g_1_1_hd':
 u'---', u'qa_contact_detail': {u'id': 20203, u'email': u'catlee@mozilla.com', u'name': u'catlee@mozilla.com', u'real_name': u'Chris AtLee [:catlee]'},
 u'priority': u'--', u'platform': u'All', u'cf_crash_signature': u'', u'version': u'unspecified', u'cf_qa_whiteboard': u'', u'cf_status_b2g_1_3t': u'--\
-', u'cf_status_firefox31': u'---', u'is_open': False, u'cf_blocking_fx': u'---', u'status': u'RESOLVED', u'cf_tracking_relnote_b2g': u'---', u'cf_stat\
us_firefox29': u'---', u'blocks': [], u'qa_contact': u'catlee@mozilla.com', u'see_also': [], u'component': u'General Automation', u'cf_tracking_firefox\
32': u'---', u'cf_tracking_firefox31': u'---', u'cf_tracking_firefox30': u'---', u'op_sys': u'All', u'groups': [], u'cf_blocking_b2g': u'---', u'target\
_milestone': u'---', u'is_cc_accessible': True, u'cf_tracking_firefox_esr24': u'---', u'cf_status_b2g_1_2': u'---', u'cf_status_b2g_1_3': u'---', u'cf_\
status_b2g18': u'---', u'cf_status_b2g_1_4': u'---', u'url': u'', u'creator_detail': {u'id': 347295, u'email': u'jgriffin@mozilla.com', u'name': u'jgri\
ffin@mozilla.com', u'real_name': u'Jonathan Griffin (:jgriffin)'}, u'whiteboard': u'', u'cf_status_b2g_2_0': u'---', u'cc_detail': [{u'id': 30066, u'em\
ail': u'coop@mozilla.com', u'name': u'coop@mozilla.com', u'real_name': u'Chris Cooper [:coop]'}, {u'id': 397261, u'email': u'dburns@mozilla.com', u'nam\
e': u'dburns@mozilla.com', u'real_name': u'David Burns :automatedtester'}, {u'id': 438921, u'email': u'jlund@mozilla.com', u'name': u'jlund@mozilla.com ', u'real_name': u'Jordan Lund (:jlund)'}, {u'id': 418814, u'email': u'mdas@mozilla.com', u'name': u'mdas@mozilla.com', u'real_name': u'Malini Das [:md\
as]'}], u'alias': None, u'cf_tracking_b2g_v1_2': u'---', u'cf_tracking_b2g_v1_3': u'---', u'flags': [], u'assigned_to': u'jgriffin@mozilla.com', u'cf_s\
tatus_firefox_esr24': u'---', u'resolution': u'FIXED', u'last_change_time': u'2014-05-30T21:20:17Z', u'cc': [u'coop@mozilla.com', u'dburns@mozilla.com'
, u'jlund@mozilla.com', u'mdas@mozilla.com'], u'cf_blocking_fennec': u'---'}]}

def test_we_cant_post_without_a_username_or_password():
    bugzilla = Bugsy()
    try:
        bugzilla.put("foo")
        assert 1 == 0, "Should have thrown when calling put"
    except BugsyException as e:
        assert str(e) == "Message: Unfortunately you can't put bugs in Bugzilla without credentials Code: None"

@responses.activate
def test_we_get_a_login_exception_when_details_are_wrong():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                      body='{"message": "The username or password you entered is not valid."}', status=400,
                      content_type='application/json', match_querystring=True)
    try:
        Bugsy("foo", "bar")
        assert 1 == 0, "Should have thrown an error"
    except LoginException as e:
        assert str(e) == "Message: The username or password you entered is not valid. Code: None"

@responses.activate
def test_bad_api_key():
    responses.add(responses.GET,
                  'https://bugzilla.mozilla.org/rest/valid_login?login=foo&api_key=badkey',
                  body='{"documentation":"http://www.bugzilla.org/docs/tip/en/html/api/","error":true,"code":306,"message":"The API key you specified is invalid. Please check that you typed it correctly."}',
                  status=400,
                  content_type='application/json', match_querystring=True)
    try:
        Bugsy(username='foo', api_key='badkey')
        assert False, 'Should have thrown'
    except LoginException as e:
        assert str(e) == 'Message: The API key you specified is invalid. Please check that you typed it correctly. Code: 306'

@responses.activate
def test_validate_api_key():
    responses.add(responses.GET,
                  'https://bugzilla.mozilla.org/rest/valid_login?login=foo&api_key=goodkey',
                  body='true', status=200, content_type='application/json',
                  match_querystring=True)
    Bugsy(username='foo', api_key='goodkey')

@responses.activate
def test_we_cant_post_without_passing_a_bug_object():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                      body='{"token": "foobar"}', status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy("foo", "bar")
    try:
        bugzilla.put("foo")
        assert 1 == 0, "Should have thrown an error about type when calling put"
    except BugsyException as e:
        assert str(e) == "Message: Please pass in a Bug object when posting to Bugzilla Code: None"

@responses.activate
def test_we_can_get_a_bug():
    responses.add(responses.GET, rest_url('bug', 1017315),
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy()
    bug = bugzilla.get(1017315)
    assert bug.id == 1017315
    assert bug.status == 'RESOLVED'
    assert bug.summary == 'Schedule Mn tests on opt Linux builds on cedar'

@responses.activate
def test_we_can_get_a_bug_with_login_token():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                        body='{"token": "foobar"}', status=200,
                        content_type='application/json', match_querystring=True)

  responses.add(responses.GET, rest_url('bug', 1017315, token='foobar'),
                    body=json.dumps(example_return), status=200,
                    content_type='application/json', match_querystring=True)
  bugzilla = Bugsy("foo", "bar")
  bug = bugzilla.get(1017315)
  assert bug.id == 1017315
  assert bug.status == 'RESOLVED'
  assert bug.summary == 'Schedule Mn tests on opt Linux builds on cedar'

@responses.activate
def test_we_can_get_username_with_userid_cookie():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/user/1234?token=1234-abcd',
                        body='{"users": [{"name": "user@example.com"}]}', status=200,
                        content_type='application/json', match_querystring=True)

  bugzilla = Bugsy(userid='1234', cookie='abcd')
  assert bugzilla.username == 'user@example.com'

@responses.activate
def test_we_can_create_a_new_remote_bug():
    bug = Bug()
    bug.summary = "I like foo"
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                      body='{"token": "foobar"}', status=200,
                      content_type='application/json', match_querystring=True)
    bug_dict = bug.to_dict().copy()
    bug_dict['id'] = 123123
    responses.add(responses.POST, 'https://bugzilla.mozilla.org/rest/bug',
                      body=json.dumps(bug_dict), status=200,
                      content_type='application/json')
    bugzilla = Bugsy("foo", "bar")
    bugzilla.put(bug)
    assert bug.id != None

@responses.activate
def test_we_can_put_a_current_bug():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                      body='{"token": "foobar"}', status=200,
                      content_type='application/json', match_querystring=True)
    bug_dict = example_return.copy()
    bug_dict['summary'] = 'I love foo but hate bar'
    responses.add(responses.PUT, 'https://bugzilla.mozilla.org/rest/bug/1017315',
                      body=json.dumps(bug_dict), status=200,
                      content_type='application/json')
    responses.add(responses.GET, rest_url('bug', 1017315, token="foobar"),
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy("foo", "bar")
    bug = Bug(**example_return['bugs'][0])
    bug.summary = 'I love foo but hate bar'
    bug.assigned_to = "automatedtester@mozilla.com"

    bugzilla.put(bug)
    assert bug.summary == 'I love foo but hate bar'
    assert bug.assigned_to == "automatedtester@mozilla.com"

@responses.activate
def test_we_handle_errors_from_bugzilla_when_posting():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                    body='{"token": "foobar"}', status=200,
                    content_type='application/json', match_querystring=True)
  responses.add(responses.POST, 'https://bugzilla.mozilla.org/rest/bug',
                    body='{"error":true,"code":50,"message":"You must select/enter a component."}', status=400,
                    content_type='application/json')

  bugzilla = Bugsy("foo", "bar")
  bug = Bug()
  try:
      bugzilla.put(bug)
      assert 1 == 0, "Put should have raised an error"
  except BugsyException as e:
      assert str(e) == "Message: You must select/enter a component. Code: 50"

@responses.activate
def test_we_handle_errors_from_bugzilla_when_updating_a_bug():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                    body='{"token": "foobar"}', status=200,
                    content_type='application/json', match_querystring=True)
  responses.add(responses.PUT, 'https://bugzilla.mozilla.org/rest/bug/1017315',
                    body='{"error":true,"code":50,"message":"You must select/enter a component."}', status=400,
                    content_type='application/json')
  bugzilla = Bugsy("foo", "bar")

  bug_dict = example_return.copy()
  bug_dict['summary'] = 'I love foo but hate bar'
  bug = Bug(**bug_dict['bugs'][0])
  try:
      bugzilla.put(bug)
  except BugsyException as e:
      assert str(e) == "Message: You must select/enter a component. Code: 50"

@responses.activate
def test_we_can_set_the_user_agent_to_bugsy():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                    body='{"token": "foobar"}', status=200,
                    content_type='application/json', match_querystring=True)
  Bugsy("foo", "bar")
  assert responses.calls[0].request.headers['User-Agent'] == "Bugsy"

@responses.activate
def test_we_can_handle_errors_when_retrieving_bugs():
    error_response = {
    "code" : 101,
    "documentation" : "http://www.bugzilla.org/docs/tip/en/html/api/",
    "error" : True,
    "message" : "Bug 111111111111 does not exist."
    }
    responses.add(responses.GET, rest_url('bug', 111111111),
                      body=json.dumps(error_response), status=404,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy()
    try:
        bug = bugzilla.get(111111111)
        assert False, "A BugsyException should have been thrown"
    except BugsyException as e:
        assert str(e) == "Message: Bug 111111111111 does not exist. Code: 101"
    except Exception as e:
        assert False, "Wrong type of exception was thrown"
