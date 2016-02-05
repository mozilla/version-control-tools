from __future__ import unicode_literals

import json
import logging

from djblets.webapi.decorators import (webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST, INVALID_ATTRIBUTE,
                                   NOT_LOGGED_IN, PERMISSION_DENIED)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.webapi.resources import WebAPIResource

from mozreview.extra_data import (
    COMMITS_KEY,
    fetch_commit_data,
    get_parent_rr,
    is_parent,
)
from mozreview.errors import (NOT_PARENT, AUTOLAND_REVIEW_NOT_APPROVED)
from mozreview.review_helpers import (gen_latest_reviews,
                                      has_shipit_carryforward)

from mozautomation.commitparser import (replace_reviewers,)


class CommitRewriteResource(WebAPIResource):
    """Provides interface to commit description rewriting."""

    name = 'commit_rewrite'
    uri_name = 'commit_rewrite'
    uri_object_key = 'review_request'
    allowed_methods = ('GET',)

    @webapi_response_errors(DOES_NOT_EXIST, INVALID_ATTRIBUTE, NOT_LOGGED_IN,
                            NOT_PARENT, PERMISSION_DENIED)
    def get(self, request, *args, **kwargs):
        try:
            parent_request = get_parent_rr(ReviewRequest.objects.get(
                id=kwargs[self.uri_object_key]))
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST
        if parent_request is None:
            return DOES_NOT_EXIST

        commit_data = fetch_commit_data(parent_request)

        if not is_parent(parent_request, commit_data):
            return NOT_PARENT
        if not parent_request.is_accessible_by(request.user):
            return PERMISSION_DENIED
        if COMMITS_KEY not in commit_data.extra_data:
            logging.error('Parent review request %s missing COMMIT_KEY'
                          % parent_request.id)
            return NOT_PARENT

        result = []
        children = json.loads(commit_data.extra_data[COMMITS_KEY])
        for child in children:
            try:
                child_request = ReviewRequest.objects.get(id=child[1])
            except ReviewRequest.DoesNotExist:
                return DOES_NOT_EXIST
            if not child_request.approved:
                return AUTOLAND_REVIEW_NOT_APPROVED

            reviewers = [
                r.user.username for r in gen_latest_reviews(child_request) if
                r.ship_it and
                r.user != child_request.submitter
            ]

            if not reviewers and child_request.approved:
                # This review request is approved (the repeated check is
                # to ensure this is guaranteed if other parts of the code
                # change) but we have an empty list of reviewers. We'll
                # assume the author has just approved this themself and
                # set r=me
                reviewers.append('me')

            # Detect if the commit has been changed since the last review.
            shipit_carryforward = has_shipit_carryforward(child_request)

            result.append({
                'commit': child[0],
                'id': child[1],
                'reviewers': reviewers,
                'shipit_carryforward': shipit_carryforward,
                'summary': replace_reviewers(child_request.description,
                                             reviewers)
            })

        return 200, {
            'commits': result,
            'total_results': len(result),
            'links': self.get_links(request=request),
        }

commit_rewrite_resource = CommitRewriteResource()
