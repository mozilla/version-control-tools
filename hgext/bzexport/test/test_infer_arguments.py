# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# bzexport is [excessively?] magical in some of its command line and comment
# processing. It does things like guessing whether a word looks like a bug
# number and things. It's nuts. So test it, to ensure that it remains nuts.

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from bzexport import infer_arguments


class TestUI(object):

    def __init__(self):
        self.debug_messages = []

    def debug(self, msg):
        self.debug_messages.append(msg)


class TestRev(object):

    def __init__(self, rev):
        self.rev = rev
        self.desc = 'bug 1234 - revision ' + rev

    def description(self):
        return self.desc


class TestRepo(object):

    def __init__(self):
        self.mq = TestMQRepo()

    def __contains__(self, key):
        return not (key.startswith("0") or key.startswith("nonrev"))

    def __getitem__(self, key):
        if key in self:
            return TestRev(key)
        raise KeyError("no such rev")

    def status(self):
        return [(), (), (), ()]


class TestMQRepo(TestRepo):

    def __init__(self):
        self.series = ['patch', 'nonrev-patch']
        self.applied = []


class TestSomething(unittest.TestCase):

    def setUp(self):
        self.ui = TestUI()
        self.repo = TestRepo()

    def call_infer_arguments(self, args, requested_opts):
        opts = {'force': None}
        opts.update(requested_opts)
        return infer_arguments(self.ui, self.repo, args, opts)

    def test_noargs(self):
        rev, bug = self.call_infer_arguments([], {})
        self.assertEqual(rev, '.')
        self.assertIsNone(bug)

    def test_both(self):
        rev, bug = self.call_infer_arguments(['funky-revision', 'named-bug'], {})
        self.assertEqual(rev, 'funky-revision')
        self.assertEqual(bug, 'named-bug')

        rev, bug = self.call_infer_arguments(['funky-revision', '888'], {})
        self.assertEqual(rev, 'funky-revision')
        self.assertEqual(bug, '888')

        # No error checking here
        rev, bug = self.call_infer_arguments(['nonrev', '888'], {})
        self.assertEqual(bug, '888')

    def test_one(self):
        # Short numbers are bugs
        rev, bug = self.call_infer_arguments(['888'], {})
        self.assertEqual(bug, '888')
        self.assertEqual(rev, '.')

        # Long numbers are revs if they are in the repo
        rev, bug = self.call_infer_arguments(['88888888888'], {})
        self.assertEqual(rev, '88888888888')
        self.assertIsNone(bug)

        # And if they aren't in the repo or mq, assume they're a bug alias. Which is weird.
        rev, bug = self.call_infer_arguments(['088888888888'], {})
        self.assertEqual(bug, '088888888888')
        self.assertEqual(rev, '.')

        # revs not in the repo but in the mq repo are mq patches. These are
        # returned in the 'rev' return slot.
        rev, bug = self.call_infer_arguments(['nonrev-patch'], {})
        self.assertEqual(rev, 'nonrev-patch')
        self.assertIsNone(bug)

if __name__ == '__main__':
    unittest.main()
