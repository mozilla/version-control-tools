from __future__ import unicode_literals

import itertools
import json
import logging

from django.contrib.auth.models import (
    User,
)
from django.db import (
    transaction,
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
    DOES_NOT_EXIST,
    INVALID_FORM_DATA,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
)
from reviewboard.reviews.errors import (
    PublishError,
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

from mozreview.bugzilla.client import (
    Bugzilla,
)
from mozreview.errors import (
    NOT_PARENT,
    REVIEW_REQUEST_UPDATE_NOT_ALLOWED,
)
from mozreview.extra_data import (
    is_parent,
    gen_child_rrs,
    set_publish_as,
    clear_publish_as,
    update_parent_rr_reviewers,
)
from mozreview.models import (
    get_bugzilla_api_key,
)


class ModifyReviewerResource(WebAPIResource):
    """Resource to modify the reviewers for a particular review request.

    We require a separate resource to handle this so we can allow
    anyone with permissions in bugzilla to modify the request.

    The reviewers JSON is in the form of:
        {
            child_rrid: [ 'reviewer1', 'reviewer2', ... ],
            ...
        }
    eg. {"5":["level1"]} updates rrid 5, clearing all existing reviewers then
        setting the reviewers to the "level1" user.
    """

    name = 'modify_reviewer'
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
            'reviewers': {
                'type': six.text_type,
                'description': 'A JSON string contining the new reviewers'
            },
        },
    )
    def create(self, request, parent_request_id, reviewers, *args, **kwargs):
        try:
            parent_rr = ReviewRequest.objects.get(pk=parent_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if not (parent_rr.is_accessible_by(request.user)
                or parent_rr.is_mutable_by(request.user)):
            return PERMISSION_DENIED

        if not is_parent(parent_rr):
            return NOT_PARENT

        # Validate and expand the new reviewer list.

        bugzilla = Bugzilla(get_bugzilla_api_key(request.user))
        child_reviewers = json.loads(reviewers)
        invalid_reviewers = []
        for child_rrid in child_reviewers:
            users = []
            for username in child_reviewers[child_rrid]:
                try:
                    users.append(bugzilla.get_user_from_irc_nick(username))
                except User.DoesNotExist:
                    invalid_reviewers.append(username)
            child_reviewers[child_rrid] = users

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

        # Review Board only supports the submitter updating a review
        # request.  In order for this to work, we publish these changes
        # in Review Board under the review submitter's account, and
        # set an extra_data field which instructs our bugzilla
        # connector to use this request's user when adjusting flags.
        #
        # Updating the review request requires creating a draft and
        # publishing it, so we have to be careful to not overwrite
        # existing drafts.

        try:
            with transaction.atomic():
                for rr in itertools.chain([parent_rr],
                                          gen_child_rrs(parent_rr)):
                    if rr.get_draft() is not None:
                        return REVIEW_REQUEST_UPDATE_NOT_ALLOWED.with_message(
                            "Unable to update reviewers as the review "
                            "request has pending changes (the patch author "
                            "has a draft)")

                try:
                    for child_rr in gen_child_rrs(parent_rr):
                        if str(child_rr.id) in child_reviewers:
                            if not child_rr.is_accessible_by(request.user):
                                return PERMISSION_DENIED.with_message(
                                    "You do not have permission to update "
                                    "reviewers on review request %s"
                                    % child_rr.id)

                            draft = ReviewRequestDraft.create(child_rr)
                            draft.target_people.clear()
                            for user in child_reviewers[str(child_rr.id)]:
                                draft.target_people.add(user)

                    set_publish_as(parent_rr, request.user)
                    parent_rr_draft = ReviewRequestDraft.create(parent_rr)
                    update_parent_rr_reviewers(parent_rr_draft)
                    parent_rr.publish(user=parent_rr.submitter)
                finally:
                    clear_publish_as(parent_rr)

        except PublishError as e:
                logging.error("failed to update reviewers on %s: %s"
                              % (parent_rr.id, str(e)))
                return PUBLISH_ERROR.with_message(str(e))

        return 200, {}

    def get_uri(self, request):
        named_url = self._build_named_url(self.name_plural)
        return request.build_absolute_uri(
            local_site_reverse(named_url, request=request, kwargs={}))

modify_reviewer_resource = ModifyReviewerResource()
