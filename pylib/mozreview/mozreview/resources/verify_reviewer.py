from __future__ import unicode_literals

from django.contrib.auth.models import (
    User,
)
from django.utils import (
    six,
)
from djblets.webapi.decorators import (
    webapi_login_required,
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.webapi.errors import (
    INVALID_FORM_DATA,
    NOT_LOGGED_IN,
)
from mozreview.bugzilla.client import (
    Bugzilla,
)
from mozreview.models import (
    get_bugzilla_api_key,
)
from reviewboard.site.urlresolvers import (
    local_site_reverse,
)
from reviewboard.webapi.resources import (
    WebAPIResource,
)


class VerifyReviewerResource(WebAPIResource):
    """Resource to check the validity of provided reviewer names."""

    allowed_methods = ('GET', 'POST')
    name = 'verify_reviewer'

    @webapi_login_required
    @webapi_response_errors(INVALID_FORM_DATA, NOT_LOGGED_IN)
    @webapi_request_fields(
        required={
            'reviewers': {
                'type': six.text_type,
                'description': 'A comma separated list of reviewers'
            },
        },
    )
    def create(self, request, reviewers, *args, **kwargs):
        bugzilla = Bugzilla(get_bugzilla_api_key(request.user))
        new_reviewers = [u.strip() for u in reviewers.split(',') if u.strip()]
        invalid_reviewers = []
        for reviewer in new_reviewers:
            try:
                bugzilla.get_user_from_irc_nick(reviewer)
            except User.DoesNotExist:
                invalid_reviewers.append(reviewer)

        if invalid_reviewers:
            # Because this isn't called through Review Board's built-in
            # backbone system, it's dramatically simpler to return just the
            # intended error message instead of categorising the errors by
            # field.
            if len(invalid_reviewers) == 1:
                return INVALID_FORM_DATA.with_message(
                    "The reviewer '%s' was not found" % invalid_reviewers[0])
            else:
                return INVALID_FORM_DATA.with_message(
                    "The reviewers '%s' were not found"
                    % "', '".join(invalid_reviewers))

        return 200, {}

    def get_uri(self, request):
        named_url = self._build_named_url(self.name_plural)
        return request.build_absolute_uri(
            local_site_reverse(named_url, request=request, kwargs={}))

verify_reviewer_resource = VerifyReviewerResource()
