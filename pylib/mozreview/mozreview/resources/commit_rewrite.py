from __future__ import unicode_literals

import json
import logging

from djblets.webapi.decorators import (webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST, INVALID_ATTRIBUTE,
                                   NOT_LOGGED_IN, PERMISSION_DENIED)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.webapi.resources import WebAPIResource

from mozreview.extra_data import (COMMITS_KEY, is_parent, get_parent_rr)
from mozreview.errors import (NOT_PARENT, AUTOLAND_REVIEW_NOT_APPROVED)
from mozreview.review_helpers import (gen_latest_reviews)


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
        if not is_parent(parent_request):
            return NOT_PARENT
        if not parent_request.is_accessible_by(request.user):
            return PERMISSION_DENIED
        if COMMITS_KEY not in parent_request.extra_data:
            logging.error('Parent review request %s missing COMMIT_KEY'
                          % parent_request.id)
            return NOT_PARENT

        result = []
        children = json.loads(parent_request.extra_data[COMMITS_KEY])
        for child in children:
            try:
                child_request = ReviewRequest.objects.get(id=child[1])
            except ReviewRequest.DoesNotExist:
                return DOES_NOT_EXIST
            if not child_request.approved:
                return AUTOLAND_REVIEW_NOT_APPROVED

            reviewers = map(lambda review: review.user.username,
                            gen_latest_reviews(child_request))
            result.append({
                'commit': child[0],
                'id': child[1],
                'reviewers': reviewers,
                'summary': replace_reviewers(child_request.description,
                                             reviewers)
            })

        return 200, {
            'commits': result,
            'total_results': len(result),
            'links': self.get_links(request=request),
        }

commit_rewrite_resource = CommitRewriteResource()
