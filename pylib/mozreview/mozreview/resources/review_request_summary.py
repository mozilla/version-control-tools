from __future__ import unicode_literals

import json
import logging

from djblets.webapi.decorators import webapi_response_errors
from djblets.webapi.errors import (DOES_NOT_EXIST, INVALID_ATTRIBUTE,
                                   NOT_LOGGED_IN, PERMISSION_DENIED)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.webapi.encoder import status_to_string
from reviewboard.webapi.resources import WebAPIResource

from mozreview.resources.errors import CHILD_DOES_NOT_EXIST, NOT_PARENT
from mozreview.utils import is_parent


def summarize_review_request(review_request, commit=None):
    d = {}

    for field in ('id', 'summary', 'last_updated', 'issue_open_count'):
        d[field] = getattr(review_request, field)

    d['submitter'] = review_request.submitter.username
    d['status'] = status_to_string(review_request.status)
    d['reviewers'] = [x.username for x in review_request.target_people.all()]

    if commit:
        d['commit'] = commit

    return d


class ReviewRequestSummaryResource(WebAPIResource):
    """Provides a summary of a parent review request and its children."""
    name = 'review_request_summary'
    uri_name = 'summary'
    uri_object_key = 'review_request'
    allowed_methods = ('GET',)

    def has_access_permissions(self, request, parent_review_request, *args,
                               **kwargs):
        return parent_review_request.is_accessible_by(request.user)

    @webapi_response_errors(CHILD_DOES_NOT_EXIST, DOES_NOT_EXIST,
                            INVALID_ATTRIBUTE, NOT_LOGGED_IN, NOT_PARENT,
                            PERMISSION_DENIED)
    def get(self, request, *args, **kwargs):
        parent_rrid = kwargs[self.uri_object_key]
        try:
            parent_review_request = ReviewRequest.objects.get(id=parent_rrid)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if not self.has_access_permissions(request, parent_review_request,
                                           *args, **kwargs):
            return self.get_no_access_error(request, parent_review_request,
                                            *args, **kwargs)

        commits_key = 'p2rb.commits'

        if not is_parent(parent_review_request):
            return NOT_PARENT

        if not parent_review_request.public:
            # Review request has never been published.
            return DOES_NOT_EXIST

        data = {
            'parent': summarize_review_request(parent_review_request),
            'children': [],
        }
        commit_tuples = json.loads(
            parent_review_request.extra_data[commits_key])

        for commit_tuple in commit_tuples:
            rrid = commit_tuple[1]
            try:
                child = ReviewRequest.objects.get(id=rrid)
            except ReviewRequest.DoesNotExist:
                logging.error('Error summarizing parent review request %s: '
                              'data for child review request %s not found'
                              % (parent_rrid, rrid))
                return CHILD_DOES_NOT_EXIST, {
                    'mozreview': {
                        'children': 'data for child review request %s not '
                                    'found' % rrid,
                    }
                }
            data['children'].append(summarize_review_request(
                child, commit_tuple[0]))

        return 200, data


review_request_summary_resource = ReviewRequestSummaryResource()
