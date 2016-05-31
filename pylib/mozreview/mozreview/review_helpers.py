# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from reviewboard.reviews.models import ReviewRequestDraft

from mozreview.extra_data import REVIEW_FLAG_KEY
from mozreview.models import get_profile


def gen_latest_reviews(review_request):
    """Generate a series of relevant reviews.

    Generates the set of reviews for a review request where there is
    only a single review for each user and it is that users most
    recent review.
    """
    last_user = None
    relevant_reviews = review_request.get_public_reviews().order_by(
        'user', '-timestamp')

    for review in relevant_reviews:
        if review.user == last_user:
            # We only care about the most recent review for each
            # particular user.
            continue

        last_user = review.user
        yield review


def has_valid_shipit(review_request):
    """Return whether the review request has received a valid ship-it.

    A boolean will be returned indicating if the review request has received
    a ship-it from any user on the reviewing users most recent review (i.e.
    a reviewer has provided a ship-it and has not since given a review
    without a ship-it).
    """
    for review in gen_latest_reviews(review_request):
        # TODO: Should we require that the ship-it comes from a review
        # which the review request submitter didn't create themselves?
        if review.ship_it:
            return True

    return False


def has_l3_shipit(review_request):
    """Return whether the review request has received a current L3 ship it.

    A boolean will be returned indicating if the review request has received
    a ship-it from an L3 user that is still valid. In order to be valid the
    ship-it must have been provided after the latest diff has been uploaded.
    """
    diffset_history = review_request.diffset_history

    if not diffset_history:
        # There aren't any published diffs so we should just consider
        # any ship-its meaningless.
        return False

    if not diffset_history.last_diff_updated:
        # Although I'm not certain when this field will be empty
        # it has "blank=true, null=True" - we'll assume there is
        # no published diff.
        return False

    for review in gen_latest_reviews(review_request):
        if not review.ship_it:
            continue
        if get_profile(review.user).has_scm_ldap_group('scm_level_3'):
            return True

    return False


def get_reviewers_status(review_request, reviewers=None,
                         include_drive_by=False):
    """Returns the latest review status for each reviewer.

    If include_drive_by is False, only reviewers nominated by the reviewee are
    considered. Set it to True to also report the status of `drive_by`
    reviewers.

    If a list of reviewers is provided, the returned dictionary will contain
    those reviewers regardless the value of include_drive_by
    """

    designated_reviewers = review_request.target_people.all()
    if not reviewers:
        reviewers = designated_reviewers

    # We need to grab the reviews and statuses off the non-draft.
    if isinstance(review_request, ReviewRequestDraft):
        review_request = review_request.review_request

    reviewers_status = dict()

    for r in reviewers:
        # The initial state is r?
        reviewers_status[r.username] = {
            'ship_it': False,
            'review_flag': 'r?' if r in designated_reviewers else ' ',
        }

    for review in gen_latest_reviews(review_request):
        review_flag = review.extra_data.get(REVIEW_FLAG_KEY)
        user = review.user.username

        if (user not in reviewers_status) and include_drive_by:
            reviewers_status[user] = {}

        if user in reviewers_status:
            reviewers_status[user]['ship_it'] = review.ship_it
            if review_flag:
                reviewers_status[user]['review_flag'] = review_flag
            else:
                # For backwards compatibility.
                if review.ship_it:
                    reviewers_status[user]['review_flag'] = 'r+'
                else:
                    reviewers_status[user]['review_flag'] = ' '

    return reviewers_status


def has_shipit_carryforward(review_request):
    """Return whether the review request has a carried forward ship-it

    A ship-it is considered carried forward if the commit for which it was
    granted has been amended since the ship-it was granted. This returns
    True if a ship-it was carried forward, and false if no ship-its are
    present or none have been carried forward.
    """
    diffset_history = review_request.diffset_history

    if not diffset_history:
        # There aren't any published diffs so we should just consider
        # any ship-its meaningless.
        return False

    if not diffset_history.last_diff_updated:
        # Although I'm not certain when this field will be empty
        # it has "blank=true, null=True" - we'll assume there is
        # no published diff.
        return False

    for review in gen_latest_reviews(review_request):
        if not review.ship_it:
            continue

        # TODO: We might want to add a required delay between when the
        # diff is posted and when a review is published - this would
        # avoid a malicious user from timing a diff publish immediately
        # before a reviewer publishes a ship-it on the previous diff
        # (Making it look like the ship-it came after the new diff)
        if review.timestamp <= diffset_history.last_diff_updated:
            return True

    return False
