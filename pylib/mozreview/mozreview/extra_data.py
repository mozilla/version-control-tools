# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

from reviewboard.reviews.models import ReviewRequest


MOZREVIEW_KEY = 'p2rb'

COMMITS_KEY = MOZREVIEW_KEY + '.commits'
COMMIT_ID_KEY = MOZREVIEW_KEY + '.commit_id'
IDENTIFIER_KEY = MOZREVIEW_KEY + '.identifier'
UNPUBLISHED_RRIDS_KEY = MOZREVIEW_KEY + '.unpublished_rids'


def get_parent_rr(review_request):
    if IDENTIFIER_KEY not in review_request.extra_data:
        return None

    return ReviewRequest.objects.get(
        commit_id=review_request.extra_data[IDENTIFIER_KEY],
        repository=review_request.repository)


def gen_child_rrs(review_request):
    """ Generate child review requests.

    For some review request (draft or normal) that has a p2rb.commits
    extra_data field, we yield the child review requests belonging to
    the review-request IDs in that field.

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
        if child:
            yield child


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
