from __future__ import unicode_literals

from djblets.webapi.decorators import (
    webapi_response_errors,
)
from djblets.webapi.errors import (
    DOES_NOT_EXIST,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
)
from reviewboard.reviews.models import (
    ReviewRequest,
)
from reviewboard.webapi.resources import (
    WebAPIResource,
)

from mozreview.models import (
    CommitData,
)


class CommitDataResource(WebAPIResource):
    """Provides read-only access to extra_data.

    This resource is primarily needed for testing to allow the contents of
    CommitData to be inspected.
    """

    name = 'commit_data'
    uri_name = 'commit-data'
    uri_object_key = 'review_request_id'
    allowed_methods = ('GET',)

    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    def get(self, request, review_request_id=None, *args, **kwargs):
        try:
            rr = ReviewRequest.objects.get(id=review_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if not rr.is_accessible_by(request.user):
            return self.get_no_access_error(request, *args, **kwargs)

        rr_draft = rr.get_draft(user=request.user)
        data, created = CommitData.objects.get_or_create(review_request=rr)

        rr_data = data.extra_data
        rr_draft_data = rr_draft and data.draft_extra_data

        return 200, {
            'review_request_id': rr.id,
            'extra_data': rr_data,
            'draft_extra_data': rr_draft_data,
        }

commit_data_resource = CommitDataResource()
