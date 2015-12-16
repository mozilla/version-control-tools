from mozhginfo.push import Push
import unittest
import json

MOCK_FULL_PUSH = """
{
    "87833": {
    "changesets": [{"author": "Chris Peterson \u003ccpeterson@mozilla.com\u003e",
    "branch": "default",
    "desc": "try: -b do -p win32,win32-mulet,win64,win32_gecko
    -u all[Windows XP,Windows 7,Windows 8,b2g] -t none",
    "files": ["main.cpp"], "node": "2dc063b51c0eea1b6b026253a2d8d3421716b197",
    "tags": ["test_tags"]}],
    "date": 1441983569,
    "user": "nobody@mozilla.com"
    }
}
"""

MOCK_SIMPLE_PUSH = """
{
    "87833": {
    "changesets": ["2dc063b51c0eea1b6b026253a2d8d3421716b197"],
    "date": 1441983569,
    "user": "nobody@mozilla.com"
    }
}
"""


class TestPush(unittest.TestCase):
    def test_full_push(self):
        data = json.loads(MOCK_FULL_PUSH.replace('\n', ''))
        push_id, push_info = data.popitem()
        push = Push(push_id=push_id, push_info=push_info)
        assert push is not None
        assert push.id == "87833"
        assert push.date == 1441983569
        assert push.user == "nobody@mozilla.com"
        changesets = push.changesets
        assert len(changesets) == 1
        assert changesets[0].node == "2dc063b51c0eea1b6b026253a2d8d3421716b197"
        assert changesets[0].desc == push_info["changesets"][0]['desc']
        assert changesets[0].files == ["main.cpp"]
        assert changesets[0].tags == ["test_tags"]

    def test_simple_push(self):
        data = json.loads(MOCK_SIMPLE_PUSH.replace('\n', ''))
        push_id, push_info = data.popitem()
        push = Push(push_id=push_id, push_info=push_info)
        assert push.changesets[0].node == "2dc063b51c0eea1b6b026253a2d8d3421716b197"
