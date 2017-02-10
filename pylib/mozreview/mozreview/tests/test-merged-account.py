# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# It is very rare to remove account by Bugzilla.
# One of such is merging user accounts. As a result old account is deleted.
# MozReview holds a table in database for BugzillaUserMap which links Mozreview
# and Bugzilla accounts. If user account was merged the link remains. In such
# case Mozreview has to provide a meaningful info.

import pytest

from mock import patch

from mozreview.bugzilla import attachments
from mozreview.errors import BugzillaUserMapError
from mozreview.tests.helpers import UserFactory


@patch.object(attachments.BugzillaUserMap.objects, 'get')
@patch('mozreview.bugzilla.attachments.get_or_create_bugzilla_users')
def test_bugzilla_usermap_excetion(mock_get_or_create_bugzilla_users,
                                   mock_bum_get):
    class ReviewRequestDraft:
        class TargetPeople:
            user = UserFactory()

            def all(self):
                return [self.user]

        diffset = None
        target_people = TargetPeople()

    class Bugzilla:
        """ Fake Bugzilla client. """
        def get_user_from_userid(self, *args):
            # No need to return any value as it is just used to pass to
            # a mocked function
            return None

    # BugzillaUserMap.objects.get should return an object with just
    # bugzilla_user_id
    class BugzillaUserMap:
        bugzilla_user_id = 1

    mock_bum_get.return_value = BugzillaUserMap()

    # mrmodels.get_or_create_bugzilla_users is returning an empty array
    # if no Bugzilla user is found
    mock_get_or_create_bugzilla_users.return_value = []

    bugzilla = Bugzilla()
    draft = ReviewRequestDraft()
    children_to_post = ((draft, None),)
    children_to_obsolete = []
    bug_id = 1

    # In case there is an entry in BugzillaUserMap and no user is found
    # in Bugzilla with given id a BugzillaUserMapError should be raised
    with pytest.raises(BugzillaUserMapError) as excinfo:
        attachments.update_bugzilla_attachments(bugzilla, bug_id,
                                                children_to_post,
                                                children_to_obsolete)
    # BugzillaUserMapError should pass the username of the non-existing
    # reviewer
    excinfo.match(draft.target_people.user.username)
