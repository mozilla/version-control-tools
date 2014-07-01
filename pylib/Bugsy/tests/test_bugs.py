import responses
import json

from bugsy import Bugsy, Bug
from bugsy import BugException

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

def test_can_create_bug_and_set_summary_afterwards():
    bug = Bug()
    assert bug.id == None, "Id has been set"
    assert bug.summary == '', "Summary is not set to nothing on plain initialisation"
    bug.summary = "Foo"
    assert bug.summary == 'Foo', "Summary is not being set"
    assert bug.status == '', 'Status has been set'

def test_we_cant_set_status_unless_there_is_a_bug_id():
    bug = Bug()
    try:
        bug.status = 'RESOLVED'
    except BugException as e:
        assert str(e) == "Message: Can not set status unless there is a bug id. Please call Update() before setting"

def test_we_can_get_OS_set_from_default():
    bug = Bug()
    assert bug.OS == "All"

def test_we_can_get_OS_we_set():
    bug = Bug(op_sys="Linux")
    assert bug.OS == "Linux"

def test_we_can_get_Product_set_from_default():
    bug = Bug()
    assert bug.product == "core"

def test_we_can_get_Product_we_set():
    bug = Bug(product="firefox")
    assert bug.product == "firefox"

def test_we_throw_an_error_for_invalid_status_types():
    bug = Bug(**example_return['bugs'][0])
    try:
        bug.status = "foo"
        assert 1 == 0, "Should have thrown an error about invalid type"
    except BugException as e:
        assert str(e) == "Message: Invalid status type was used"

def test_we_can_get_the_resolution():
    bug = Bug(**example_return['bugs'][0])
    assert "FIXED" == bug.resolution

def test_we_can_set_the_resolution():
    bug = Bug(**example_return['bugs'][0])
    bug.resolution = 'INVALID'
    assert bug.resolution == 'INVALID'

def test_we_cant_set_the_resolution_when_not_valid():
    bug = Bug(**example_return['bugs'][0])
    try:
        bug.resolution = 'FOO'
        assert 1==0, "Should thrown an error"
    except BugException as e:
        assert str(e) == "Message: Invalid resolution type was used"

def test_we_can_pass_in_dict_and_get_a_bug():
    bug = Bug(**example_return['bugs'][0])
    assert bug.id == 1017315
    assert bug.status == 'RESOLVED'
    assert bug.summary == 'Schedule Mn tests on opt Linux builds on cedar'

def test_we_can_get_a_dict_version_of_the_bug():
    bug = Bug(**example_return['bugs'][0])
    result = bug.to_dict()
    assert example_return['bugs'][0]['id'] == result['id']

@responses.activate
def test_we_can_update_a_bug_from_bugzilla():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315',
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy()
    bug = bugzilla.get(1017315)
    import copy
    bug_dict = copy.deepcopy(example_return)
    bug_dict['bugs'][0]['status'] = "REOPENED"
    responses.reset()
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315',
                      body=json.dumps(bug_dict), status=200,
                      content_type='application/json')
    bug.update()
    assert bug.status == 'REOPENED'

def test_we_cant_update_unless_we_have_a_bug_id():
    bug = Bug()
    try:
        bug.update()
    except BugException as e:
        assert str(e) == "Message: Unable to update bug that isn't in Bugzilla"

@responses.activate
def test_we_can_update_a_bug_with_login_token():
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                        body='{"token": "foobar"}', status=200,
                        content_type='application/json', match_querystring=True)

  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315?token=foobar',
                    body=json.dumps(example_return), status=200,
                    content_type='application/json', match_querystring=True)
  bugzilla = Bugsy("foo", "bar")
  bug = bugzilla.get(1017315)
  import copy
  bug_dict = copy.deepcopy(example_return)
  bug_dict['bugs'][0]['status'] = "REOPENED"
  responses.reset()
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315?token=foobar',
                    body=json.dumps(bug_dict), status=200,
                    content_type='application/json', match_querystring=True)
  bug.update()
  assert bug.id == 1017315
  assert bug.status == 'REOPENED'
  assert bug.summary == 'Schedule Mn tests on opt Linux builds on cedar'

@responses.activate
def test_that_we_can_add_a_comment_to_a_bug():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                          body='{"token": "foobar"}', status=200,
                          content_type='application/json', match_querystring=True)

    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315?token=foobar',
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy("foo", "bar")
    bug = bugzilla.get(1017315)
    bug.add_comment("I like sausages")

    responses.add(responses.POST, 'https://bugzilla.mozilla.org/rest/bug/1017315?token=foobar',
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla.put(bug)
