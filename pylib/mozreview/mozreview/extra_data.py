# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import re

from reviewboard.changedescs.models import ChangeDescription
from reviewboard.reviews.models import (
    ReviewRequest,
    ReviewRequestDraft,
)

from mozreview.models import (
    CommitData,
)

MOZREVIEW_KEY = 'p2rb'

BASE_COMMIT_KEY = MOZREVIEW_KEY + '.base_commit'
COMMITS_KEY = MOZREVIEW_KEY + '.commits'
DISCARD_ON_PUBLISH_KEY = MOZREVIEW_KEY + '.discard_on_publish_rids'
REVIEWER_MAP_KEY = MOZREVIEW_KEY + '.reviewer_map'
SQUASHED_KEY = MOZREVIEW_KEY + '.is_squashed'
UNPUBLISHED_KEY = MOZREVIEW_KEY + '.unpublished_rids'

# CommitData field keys:
COMMIT_ID_KEY = MOZREVIEW_KEY + '.commit_id'
FIRST_PUBLIC_ANCESTOR_KEY = MOZREVIEW_KEY + '.first_public_ancestor'
IDENTIFIER_KEY = MOZREVIEW_KEY + '.identifier'

# CommitData fields which should be automatically copied from
# draft_extra_data to extra_data when a review request is published.
DRAFTED_COMMIT_DATA_KEYS = (
    FIRST_PUBLIC_ANCESTOR_KEY,
    IDENTIFIER_KEY,
    COMMIT_ID_KEY,
)

REVIEWID_RE = re.compile('bz://(\d+)/[^/]+')


def fetch_commit_data(review_request_details, commit_data=None):
    """fetch the CommitData object associated with a review request details

    If a CommitData object is also provided we will verify that it represents
    the provided review_request_details.
    """
    is_draft = isinstance(review_request_details, ReviewRequestDraft)

    if commit_data is None and is_draft:
        commit_data = CommitData.objects.get_or_create(
            review_request_id=review_request_details.review_request_id)[0]
    elif commit_data is None:
        commit_data = CommitData.objects.get_or_create(
            review_request_id=review_request_details.id)[0]
    elif is_draft:
        assert (commit_data.review_request_id ==
                review_request_details.review_request_id)
    else:
        assert commit_data.review_request_id == review_request_details.id

    return commit_data


def is_pushed(review_request, commit_data=None):
    """Is this a review request that was pushed to MozReview."""
    commit_data = fetch_commit_data(review_request, commit_data=commit_data)

    is_draft = isinstance(review_request, ReviewRequestDraft)
    return ((not is_draft and IDENTIFIER_KEY in commit_data.extra_data) or
            (is_draft and IDENTIFIER_KEY in commit_data.draft_extra_data))


def is_parent(review_request, commit_data=None):
    """Is this a MozReview 'parent' review request.

    If this review request represents the folded diff parent of each child
    review request we will return True. This will return false on each of the
    child review requests (or a request which was not pushed).

    TODO: Use commit_data when SQUASHED_KEY is migrated to
    CommitData.
    """
    return str(review_request.extra_data.get(
        SQUASHED_KEY, False)).lower() == 'true'


def get_parent_rr(review_request_details, commit_data=None):
    """Retrieve the `review_request` parent.

    If `review_request` is a parent, return it directly.
    Otherwise return its parent based on the identifier in extra_data.
    """
    commit_data = fetch_commit_data(review_request_details, commit_data)

    if not is_pushed(review_request_details, commit_data):
        return None

    if is_parent(review_request_details, commit_data):
        return review_request_details

    identifier = commit_data.get_for(review_request_details, IDENTIFIER_KEY)

    return ReviewRequest.objects.get(
        commit_id=identifier,
        repository=review_request_details.repository)


def gen_child_rrs(review_request, user=None):
    """ Generate child review requests.

    For some review request (draft or normal) that has a p2rb.commits
    extra_data field, we yield the child review requests belonging to
    the review-request IDs in that field.

    If a user instance is given, a check is performed to guarantee that
    the user has access to each child. If the user has access to the draft
    version of a child, the draft will be returned.

    If a review request is not found for the listed ID, get_rr_for_id will
    log this, and we'll skip that ID.
    """
    if COMMITS_KEY not in review_request.extra_data:
        return

    commit_tuples = json.loads(review_request.extra_data[COMMITS_KEY])
    for commit_tuple in commit_tuples:
        child = get_rr_for_id(commit_tuple[1])

        # TODO: We should fail if we can't find a child; it indicates
        # something very bad has happened.  Unfortunately this call is
        # used in several different contexts, so we need to make changes
        # there as well.
        if not child:
            continue
        elif user is None:
            yield child
        elif child.is_accessible_by(user):
            yield child.get_draft(user) or child


def gen_rrs_by_extra_data_key(review_request, key):
    if key not in review_request.extra_data:
        return

    return gen_rrs_by_rids(json.loads(review_request.extra_data[key]))


def gen_rrs_by_rids(rrids):
    for rrid in rrids:
        review_request = get_rr_for_id(rrid)
        if review_request:
            yield review_request


def get_rr_for_id(id):
    try:
        return ReviewRequest.objects.get(pk=id)
    except ReviewRequest.DoesNotExist:
        logging.error('Could not retrieve child review request with '
                      'id %s because it does not appear to exist.'
                      % id)


def update_parent_rr_reviewers(parent_rr_draft):
    """Update the list of reviewers on a parent draft.

    We first retrieve a list of the (possibly draft) children and then we
    build a list of unique reviewers related to them.
    We also store a map of the reviewers grouped by children in the parent's
    extra_data. In this way we can publish a parent draft even if the only
    change is on the reviewer list of one of the children.
    """
    # TODO: Add an optional child_rr_draft parameter to speed things up when we know
    # which child changed.
    child_rr_list = gen_child_rrs(parent_rr_draft)
    reviewers_map_before = parent_rr_draft.extra_data.get(REVIEWER_MAP_KEY, None)

    reviewers_map_after = {}

    for child in child_rr_list:
        actual_child = child.get_draft() or child
        reviewers = actual_child.target_people.values_list(
            'id', flat=True).order_by('id')
        reviewers_map_after[str(child.id)] = list(reviewers)

    if reviewers_map_after != reviewers_map_before:
        total_reviewers = set(sum(reviewers_map_after.values(), []))
        parent_rr_draft.target_people = total_reviewers
        parent_rr_draft.extra_data[REVIEWER_MAP_KEY] = json.dumps(reviewers_map_after)

        parent_rr = parent_rr_draft.get_review_request()
        if parent_rr.public and parent_rr_draft.changedesc is None:
            parent_rr_draft.changedesc = ChangeDescription.objects.create()

        parent_rr_draft.save()
