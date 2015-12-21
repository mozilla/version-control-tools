import json
import unittest

from mock import patch, Mock
from mozhginfo import pushlog_client
from mozhginfo.push import Push
from mozhginfo.pushlog_client import (
    query_pushes_by_specified_revision_range,
    query_pushes_by_pushid_range,
    query_pushes_by_revision_range,
    query_push_by_revision,
    query_repo_tip,
)

LIST_REVISION = """
{
    "lastpushid": 67951,
    "pushes": {
    "53348":{"changesets": ["eb15e3f893453d6a4472f8905271aba33f8b68d5"],
    "date": 1419851870, "user": "nobody@mozilla.com"},
    "53349": {"changesets": ["1c5b4332e2f1b73fe03977b69371e9a08503bff3"],
    "date": 1419852144, "user": "nobody@gmail.com"},
    "53350": {"changesets": ["724f0a71d62171da1357e6c1f93453359e54206b"],
    "date": 1419853433, "user": "nobody@mozilla.com"}
    }
}
"""

REVISION_INFO_REPOSITORIES = """{
    "87833": {
    "changesets": ["71e69424094d2f86c51ba544fd861d65a578a0f2"],
    "date": 1441983569,
    "user": "nobody@mozilla.com"
    }
}
"""

INVALID_REVISION = """
"unknown revision '123456123456s'"
"""

GOOD_REVISION = """
{
 "82366": {
  "changesets": [
   "4e030c8cf8c35158c9924f6bb33ffe8af00c162b"
  ],
  "date": 1438992451,
  "user": "nobody@mozilla.com"
 }
}
"""


def mock_response(content, status):
    """Mock of requests.get()."""
    response = Mock()
    response.content = content

    def mock_response_json():
        return json.loads(content)

    response.json = mock_response_json
    response.status_code = status
    response.reason = 'OK'
    return response


class TestQueries(unittest.TestCase):
    # Mock response for query_push_by_revision
    push_id, push_info = json.loads(REVISION_INFO_REPOSITORIES).popitem()
    push = Push(push_id=push_id, push_info=push_info)
    MOCK_PUSH = json.dumps(json.loads(LIST_REVISION)['pushes'])

    def setUp(self):
        self.repo_url = "https://hg.mozilla.org/integration/mozilla-inbound"
        self.revision = '71e69424094d'
        self.start_revision = '8850aa0f93453d6a4472f8905271aba33f8b68d5'
        self.end_revision = '2a193b7fd62171da1357e6c1f93453359e54206b'

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    @patch('mozhginfo.pushlog_client.query_push_by_revision',
           return_value=push)
    def test_query_pushes_by_revision_range(self, get, query_push_by_revision):
        pushes = query_pushes_by_revision_range(repo_url=self.repo_url,
                                                from_revision=self.start_revision,
                                                to_revision=self.end_revision,
                                                version=2, tipsonly=1)
        assert len(pushes) == 4
        push_id_list = []
        changeset_list = []
        # We want to ensure the push list we got is ordered.
        for push in pushes:
            push_id_list.append(push.id)
            changeset_list.append(push.changesets[0].node)
        assert push_id_list == ['87833', '53348', '53349', '53350']
        assert changeset_list == ['71e69424094d2f86c51ba544fd861d65a578a0f2',
                                  'eb15e3f893453d6a4472f8905271aba33f8b68d5',
                                  '1c5b4332e2f1b73fe03977b69371e9a08503bff3',
                                  '724f0a71d62171da1357e6c1f93453359e54206b']

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    def test_query_pushes_by_pushid_range(self, get):
        pushes = query_pushes_by_pushid_range(repo_url=self.repo_url, start_id=55560,
                                              end_id=55564)
        assert len(pushes) == 3

        # Duplicate with test_query_pushes_by_revision_range,
        # but I don't think we need to write a separate function for it.
        push_id_list = []
        changeset_list = []
        for push in pushes:
            push_id_list.append(push.id)
            changeset_list.append(push.changesets[0].node)
        assert push_id_list == ['53348', '53349', '53350']
        assert changeset_list == ['eb15e3f893453d6a4472f8905271aba33f8b68d5',
                                  '1c5b4332e2f1b73fe03977b69371e9a08503bff3',
                                  '724f0a71d62171da1357e6c1f93453359e54206b']

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    @patch('mozhginfo.pushlog_client.query_push_by_revision', return_value=push)
    def test_query_pushes_by_specified_revision_range(self, get, query_push_by_revision):
        pushes = query_pushes_by_specified_revision_range(repo_url=self.repo_url,
                                                          revision=self.revision,
                                                          before=1,
                                                          after=1)
        # This part is totally duplicate with the test_query_pushes_by_pushid_range,
        # because we are calling query_pushes_by_pushid_range inside this function.
        assert len(pushes) == 3
        push_id_list = []
        changeset_list = []
        for push in pushes:
            push_id_list.append(push.id)
            changeset_list.append(push.changesets[0].node)

        assert push_id_list == ['53348', '53349', '53350']
        assert changeset_list == ['eb15e3f893453d6a4472f8905271aba33f8b68d5',
                                  '1c5b4332e2f1b73fe03977b69371e9a08503bff3',
                                  '724f0a71d62171da1357e6c1f93453359e54206b']

    @patch('requests.get', return_value=mock_response(REVISION_INFO_REPOSITORIES, 200))
    def test_query_push_by_revision(self, get):
        push = query_push_by_revision(repo_url=self.repo_url, revision=self.revision)
        assert push is not None
        assert push.id == '87833'
        assert len(push.changesets) == 1
        changeset = push.changesets[0]
        assert changeset.node == "71e69424094d2f86c51ba544fd861d65a578a0f2"

    @patch('requests.get', return_value=mock_response(MOCK_PUSH, 200))
    def test_query_repo_tip(self, get):
        push = query_repo_tip(repo_url=self.repo_url)
        assert push is not None
        assert push.id == '53350'
        assert push.changesets[0].node == '724f0a71d62171da1357e6c1f93453359e54206b'


class TestValidRevision(unittest.TestCase):

    """Test valid_revision mocking GET requests."""

    @patch('requests.get', return_value=mock_response(GOOD_REVISION, 200))
    def test_valid_without_any_cache(self, get):
        """Calling the function without in-memory cache."""
        # Making sure the original cache is empty
        pushlog_client.VALID_CACHE = {}
        self.assertEquals(
            pushlog_client.valid_revision("try", "4e030c8cf8c3"), True)

        # The in-memory cache should be filed now
        self.assertEquals(
            pushlog_client.VALID_CACHE, {("try", "4e030c8cf8c3"): True})

    @patch('requests.get', return_value=mock_response(GOOD_REVISION, 200))
    def test_in_memory_cache(self,  get):
        """Calling the function with in-memory cache should return without calling request.get."""
        pushlog_client.VALID_CACHE = {("try", "146071751b1e"): True}
        self.assertEquals(
            pushlog_client.valid_revision("try", "146071751b1e"), True)

        assert get.call_count == 0

    @patch('requests.get', return_value=mock_response(INVALID_REVISION, 200))
    def test_invalid(self, get):
        """Calling the function with a bad revision."""
        self.assertEquals(
            pushlog_client.valid_revision("try", "123456123456"), False)
