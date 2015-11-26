import json
import unittest

from mock import patch, Mock
from mozhginfo import pushlog_client
from mozhginfo.pushlog_client import (
    query_revisions_range,
    query_revision_info,
    query_full_revision_info,
    query_pushid_range,
    query_repo_tip,
    query_revisions_range_from_revision_before_and_after
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

    def setUp(self):
        self.repo_url = "https://hg.mozilla.org/integration/mozilla-inbound"
        self.revision = '71e69424094d'
        self.start_revision = '8850aa0f93453d6a4472f8905271aba33f8b68d5'
        self.end_revision = '2a193b7fd62171da1357e6c1f93453359e54206b'

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    def test_query_revisions_range(self, get):
        self.assertEqual(
            query_revisions_range(self.repo_url, self.start_revision,
                                  self.end_revision, version=2, tipsonly=1),
            ['8850aa0f93453d6a4472f8905271aba33f8b68d5', 'eb15e3f893453d6a4472f8905271aba33f8b68d5',
             '1c5b4332e2f1b73fe03977b69371e9a08503bff3', '724f0a71d62171da1357e6c1f93453359e54206b']
        )

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    def test_query_pushid_range(self, get):
        self.assertEqual(
            query_pushid_range(self.repo_url, 55560, 55564),
            ['724f0a71d62171da1357e6c1f93453359e54206b', '1c5b4332e2f1b73fe03977b69371e9a08503bff3',
             'eb15e3f893453d6a4472f8905271aba33f8b68d5']
        )

    @patch('requests.get', return_value=mock_response(REVISION_INFO_REPOSITORIES, 200))
    def test_query_revision_info(self, get):
        push_info = {"date": 1441983569,
                     "changesets": ["71e69424094d2f86c51ba544fd861d65a578a0f2"],
                     "pushid": "87833",
                     "user": "nobody@mozilla.com"}
        self.assertEqual(
            query_revision_info(self.repo_url, self.revision), push_info)

    @patch('requests.get', return_value=mock_response(REVISION_INFO_REPOSITORIES, 200))
    def test_query_full_revision_info(self, get):
        self.assertEqual(
            query_full_revision_info(self.repo_url, '71e69424094'),
            '71e69424094d2f86c51ba544fd861d65a578a0f2'
        )

    @patch('requests.get', return_value=mock_response(REVISION_INFO_REPOSITORIES, 200))
    def test_query_repo_tip(self, get):
        self.assertEqual(
            query_repo_tip(self.repo_url), "71e69424094d2f86c51ba544fd861d65a578a0f2")

    @patch('requests.get', return_value=mock_response(LIST_REVISION, 200))
    @patch('mozhginfo.pushlog_client.query_revision_info', return_value={"pushid": "55561"})
    def test_query_revisions_range_from_revision_before_and_after(self, query_revision_info, get):
        self.assertEqual(
            query_revisions_range_from_revision_before_and_after(self.repo_url, self.revision,
                                                                 1, 1),
            ['724f0a71d62171da1357e6c1f93453359e54206b', '1c5b4332e2f1b73fe03977b69371e9a08503bff3',
             'eb15e3f893453d6a4472f8905271aba33f8b68d5']
        )


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
