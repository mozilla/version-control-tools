from . import rest_url
from .test_bugs import comments_return, example_return
from bugsy import (Bugsy, Bug)
from bugsy.errors import (BugsyException, LoginException)

import pytest
import responses
import json

@responses.activate
def test_an_exception_is_raised_when_we_hit_an_error():
    responses.add(responses.GET, rest_url('bug', 1017315),
                      body="It's all broken", status=500,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy()
    with pytest.raises(BugsyException) as e:
        bugzilla.get(1017315)
    assert str(e.value) == "Message: We received a 500 error with the following: It's all broken"


@responses.activate
def test_bugsyexception_raised_for_http_502_when_retrieving_bugs():
    responses.add(responses.GET, rest_url('bug', 123456),
                  body='Bad Gateway', status=502,
                  content_type='text/html', match_querystring=True)
    bugzilla = Bugsy()
    with pytest.raises(BugsyException) as e:
        r = bugzilla.get(123456)
    assert str(e.value) == "Message: We received a 502 error with the following: Bad Gateway"


@responses.activate
def test_bugsyexception_raised_for_http_503_when_verifying_api_key():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/valid_login',
                  body='Service Unavailable', status=503, content_type='text/html')
    with pytest.raises(BugsyException) as e:
        Bugsy(username='foo', api_key='goodkey')
    assert str(e.value) == "Message: We received a 503 error with the following: Service Unavailable"


@responses.activate
def test_bugsyexception_raised_for_http_500_when_commenting_on_a_bug():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                  body='{"token": "foobar"}', status=200,
                  content_type='application/json', match_querystring=True)
    responses.add(responses.GET, rest_url('bug', 1017315, token='foobar'),
                  body=json.dumps(example_return), status=200,
                  content_type='application/json', match_querystring=True)
    bugzilla = Bugsy("foo", "bar")
    bug = bugzilla.get(1017315)

    responses.add(responses.POST, 'https://bugzilla.mozilla.org/rest/bug/1017315/comment?token=foobar',
                      body='Internal Server Error', status=500,
                      content_type='text/html', match_querystring=True)
    with pytest.raises(BugsyException) as e:
        bug.add_comment("I like sausages")
    assert str(e.value) == "Message: We received a 500 error with the following: Internal Server Error"


@responses.activate
def test_bugsyexception_raised_for_http_500_when_adding_tags_to_bug_comments():
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                          body='{"token": "foobar"}', status=200,
                          content_type='application/json', match_querystring=True)

    responses.add(responses.GET, rest_url('bug', 1017315, token='foobar'),
                      body=json.dumps(example_return), status=200,
                      content_type='application/json', match_querystring=True)
    bugzilla = Bugsy("foo", "bar")
    bug = bugzilla.get(1017315)

    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug/1017315/comment?token=foobar',
                    body=json.dumps(comments_return), status=200,
                    content_type='application/json', match_querystring=True)

    comments = bug.get_comments()

    responses.add(responses.PUT, 'https://bugzilla.mozilla.org/rest/bug/comment/8589785/tags?token=foobar',
                    body='Internal Server Error', status=500,
                    content_type='text/html', match_querystring=True)
    with pytest.raises(BugsyException) as e:
        comments[0].add_tags("foo")
    assert str(e.value) == "Message: We received a 500 error with the following: Internal Server Error"
