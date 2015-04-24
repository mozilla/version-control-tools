from __future__ import unicode_literals

import json

from collections import defaultdict

from django.db.models import Q
from djblets.webapi.decorators import (webapi_response_errors,
                                       webapi_request_fields)
from djblets.webapi.errors import (DOES_NOT_EXIST, INVALID_ATTRIBUTE,
                                   NOT_LOGGED_IN, PERMISSION_DENIED)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.webapi.encoder import status_to_string
from reviewboard.webapi.resources import WebAPIResource

from mozreview.extra_data import (COMMITS_KEY,
                                  COMMIT_ID_KEY,
                                  MOZREVIEW_KEY,
                                  gen_child_rrs,
                                  get_parent_rr)
from mozreview.models import BugzillaUserMap
from mozreview.resources.errors import NOT_PARENT
from mozreview.extra_data import is_parent


class ReviewRequestSummaryResource(WebAPIResource):
    """Provides a summary of a parent review request and its children."""

    name = 'review_request_summary'
    name_plural = 'review_request_summaries'
    uri_name = 'summary'
    uri_object_key = 'review_request'
    allowed_methods = ('GET',)

    def has_access_permissions(self, request, parent_review_request, *args,
                               **kwargs):
        return parent_review_request.is_accessible_by(request.user)

    def get_queryset(self, request, is_list=False, *args, **kwargs):
        """Return public MozReview review requests.

        Takes an optional 'bug' parameter to narrow down the list to only
        those matching that bug ID.

        Note that this presumes that bugs_closed only ever contains one
        bug, which in MozReview, at the moment, is always true.
        """
        q = Q(extra_data__contains=MOZREVIEW_KEY)

        # TODO: Then may get slow as the db size increase, particularly
        # when we support multiple bugs in one parent.  We should use a
        # separate table to optimize this process.

        if is_list:
            if 'bug' in request.GET:
                q = q & Q(bugs_closed=request.GET.get('bug'))

        queryset = ReviewRequest.objects.public(
            status=None,
            extra_query=q
        )

        return queryset

    @webapi_response_errors(DOES_NOT_EXIST, INVALID_ATTRIBUTE, NOT_LOGGED_IN,
                            NOT_PARENT, PERMISSION_DENIED)
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

        if not is_parent(parent_review_request):
            return NOT_PARENT

        if not parent_review_request.public:
            # Review request has never been published.
            return DOES_NOT_EXIST

        families = self._sort_families(request, [parent_review_request])
        self._sort_families(request, gen_child_rrs(parent_review_request),
                            families=families)

        # FIXME: The returned data should actually be a dict, with keys
        # 'stat' and self.item_result_key mapped to 'ok' and the
        # family-summary dict, respectively, to match the standard Review
        # Board web API format.
        # However, the Bugzilla extension uses the existing, nonstandard
        # return value, so we have to wait until it is fetching review
        # requests by bug before fixing this.

        return 200, self._summarize_families(request, families)[0]

    @webapi_request_fields(
        optional={
            'bug': {
                'type': int,
                'description': 'Review requests must be associated with this '
                               'bug ID',
            }
        }
    )
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_ATTRIBUTE, NOT_LOGGED_IN,
                            NOT_PARENT, PERMISSION_DENIED)
    def get_list(self, request, *args, **kwargs):
        if not self.has_list_access_permissions(request, *args, **kwargs):
            return self.get_no_access_error(request, *args, **kwargs)

        try:
            queryset = self.get_queryset(request, is_list=True, *args,
                                         **kwargs)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        # Sort out the families.
        families = self._sort_families(request, queryset)
        missing_rrids = set()

        # Verify that we aren't missing any review requests.  We want
        # complete families, even if some do not match the requested bug,
        # i.e., if some children are associated with different bugs.
        # Because a few old review requests are currently in weird states,
        # and since all review requests in a given family should currently
        # have the same bug ID; we skip this part if we can't get COMMITS_KEY
        # out of the parent's extra_data.
        for parent_id, family in families.iteritems():
            if family['parent'] and COMMITS_KEY in family['parent'].extra_data:
                commit_tuples = json.loads(
                    family['parent'].extra_data[COMMITS_KEY])
                [missing_rrids.add(child_rrid) for sha, child_rrid in
                 commit_tuples if child_rrid not in family['children']]
            else:
                missing_rrids.add(parent_id)

        self._sort_families(
            request, ReviewRequest.objects.filter(id__in=missing_rrids),
            families=families)

        summaries = self._summarize_families(request, families)

        data = {
            self.list_result_key: summaries,
            'total_results': len(summaries),
            'links': self.get_links(request=request)
        }

        return 200, data

    def _sort_families(self, request, rrs, families=None):
        """Sort ReviewRequest objects into families.

        'families' is a dict with parent ReviewRequest ids as keys.  Each
        value is another dict, with 'parent' mapped to the parent
        ReviewRequest and 'children' mapped to a list of child ReviewRequests
        of that parent.  If 'families' is not None, it is updated in place;
        if 'families' is not given, it is first initialized.  In both cases
        'families' is also returned.

        For each ReviewRequest in rrs, 'families' is updated appropriately
        to assemble a full set of families.
        """
        if families is None:
            families = defaultdict(lambda: dict(parent=None, children={}))

        for rr in rrs:
            if not self.has_access_permissions(request, rr):
                continue

            if is_parent(rr):
                families[rr.id]['parent'] = rr
            else:
                # Some early review requests were orphaned; ignore them.
                try:
                    parent_rr = get_parent_rr(rr)
                except ReviewRequest.DoesNotExist:
                    continue

                families[parent_rr.id]['children'][rr.id] = rr

        return families

    def _summarize_review_request(self, request, review_request, commit=None):
        """Returns a dict summarizing a ReviewRequest object.

        Example return value for a child request (a parent looks the same but
        without a 'commit' key):

        {
            'commit': 'ece2029d013af68f9f32aa0a6199fcb2201d5aae',
            'id': 3,
            'issue_open_count': 0,
            'last_updated': '2015-04-13T18:58:25Z',
            'links': {
                    'self': {
                        'href': 'http://127.0.0.1:50936/api/extensions/mozreview.extension.MozReviewExtension/summary/3/',
                        'method': 'GET'
                    }
            },
            'reviewers': [
                'jrandom'
            ],
            'status': 'pending',
            'submitter': 'mcote',
            'summary': 'Bug 1 - Update README.md.'
        }
        """
        reviewers = list(review_request.target_people.all())
        d = {}

        for field in ('id', 'summary', 'last_updated', 'issue_open_count'):
            d[field] = getattr(review_request, field)

        # TODO: 'submitter' and 'submitter_bmo_id' should be combined into one
        # attribute, likewise with 'reviewers' and 'reviewers_bmo_ids'.  See
        # bug 1164756.
        d['submitter'] = review_request.submitter.username
        d['submitter_bmo_id'] = BugzillaUserMap.objects.get(
            user_id=review_request.submitter.id).bugzilla_user_id
        d['status'] = status_to_string(review_request.status)

        d['reviewers'] = [reviewer.username for reviewer in reviewers]
        d['reviewers_bmo_ids'] = [bzuser.bugzilla_user_id for bzuser in
                                  BugzillaUserMap.objects.filter(user_id__in=[
                                      reviewer.id for reviewer in reviewers])]

        d['links'] = self.get_links(obj=review_request, request=request)

        if commit:
            d['commit'] = commit

        return d

    def _summarize_families(self, request, families):
        """Returns a list of dicts summarizing a parent and its children.

        'families' should be a list of dicts, each containing a 'parent' key
        mapping to a single ReviewRequest and a 'children' key containing a
        list of ReviewRequests.

        Each dict in the returned list also has a 'parent' key, mapped to a
        summarized ReviewRequest, and a 'children' key, mapped to a list of
        summarized ReviewRequests. See the docstring for
        _summarize_review_request() for an example of a summarized
        ReviewRequest.
        """
        summaries = []

        for family in families.itervalues():
            summaries.append({
                'parent': self._summarize_review_request(
                    request, family['parent']),
                'children': [
                    self._summarize_review_request(
                        request, child, child.extra_data[COMMIT_ID_KEY])
                    for child in family['children'].values()
                ]
            })

        return summaries


review_request_summary_resource = ReviewRequestSummaryResource()
