from __future__ import unicode_literals

from django.db import (
    transaction,
)
from djblets.webapi.decorators import (
    webapi_login_required,
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.webapi.errors import (
    DOES_NOT_EXIST, INVALID_FORM_DATA,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
)
from reviewboard.reviews.models import (
    ReviewRequest,
    ReviewRequestDraft,
)
from reviewboard.site.urlresolvers import (
    local_site_reverse,
)
from reviewboard.webapi.errors import (
    PUBLISH_ERROR,
)
from reviewboard.webapi.resources import (
    WebAPIResource,
)

from mozreview.errors import (
    NOT_PARENT,
)
from mozreview.extra_data import (
    is_parent,
    gen_child_rrs,
)


class EnsureDraftsResource(WebAPIResource):
    """Ensure drafts exist for each child request.

    This causes Review Board to show the draft banner on the parent and all
    children when any child is updated.
    """

    name = 'ensure_draft'
    allowed_methods = ('GET', 'POST',)

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            PUBLISH_ERROR, NOT_PARENT,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'parent_request_id': {
                'type': int,
                'description': 'The parent review request to update',
            },
        },
    )
    def create(self, request, parent_request_id, *args, **kwargs):
        try:
            parent_rr = ReviewRequest.objects.get(pk=parent_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if not (parent_rr.is_accessible_by(request.user)
                or parent_rr.is_mutable_by(request.user)):
            return PERMISSION_DENIED

        if not is_parent(parent_rr):
            return NOT_PARENT

        with transaction.atomic():
            for child_rr in gen_child_rrs(parent_rr):
                if child_rr.get_draft() is None:
                    ReviewRequestDraft.create(child_rr)
            if parent_rr.get_draft() is None:
                ReviewRequestDraft.create(parent_rr)

        return 200, {}

    def get_uri(self, request):
        named_url = self._build_named_url(self.name_plural)
        return request.build_absolute_uri(
            local_site_reverse(named_url, request=request, kwargs={}))

ensure_drafts_resource = EnsureDraftsResource()
