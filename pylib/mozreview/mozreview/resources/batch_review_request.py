from __future__ import absolute_import, unicode_literals

import json
import logging

from django.db import transaction
from djblets.webapi.decorators import (
    webapi_login_required,
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.webapi.errors import (
    INVALID_FORM_DATA,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
)
from reviewboard.diffviewer.models import (
    DiffSet,
)
from reviewboard.reviews.models import (
    ReviewRequest,
    ReviewRequestDraft,
)
from reviewboard.scmtools.models import (
    Repository,
)
from reviewboard.webapi.decorators import (
    webapi_check_local_site,
)
from reviewboard.webapi.resources import (
    WebAPIResource,
)


logger = logging.getLogger(__name__)


class DiffProcessingException(Exception):
    pass


class BatchReviewRequestResource(WebAPIResource):
    """Resource for creating a series of review requests with a single request.

    Submitting multiple review requests using the traditional Web API requires
    several HTTP requests and the count grows in proportion to the number of
    review requests being submitted. In addition, changes are only atomic
    within each HTTP request. This API exists to make submitting a review
    series a single HTTP request while also being atomic.
    """
    name = 'batch_review_request'
    allowed_methods = ('GET', 'POST',)

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(INVALID_FORM_DATA, NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'repo_id': {
                'type': int,
                'description': 'Repository to which to submit reviews',
            },
            'identifier': {
                'type': str,
                'description': 'Identifier to use for this review request',
            },
            'commits': {
                'type': str,
                'description': 'JSON describing commits to submit.',
            },
        })
    def create(self, request, repo_id, identifier, commits,
               local_site_name=None, **kwargs):
        """Create or update a review request series."""
        user = request.user
        local_site = self._get_local_site(local_site_name)
        logger.info('processing BatchReviewRequest for %s' % user)

        try:
            commits = json.loads(commits)
        except ValueError:
            logger.error('invalid JSON in commits field')
            return INVALID_FORM_DATA, {'fields': {'commits': 'Not valid JSON.'}}

        if not isinstance(commits, dict):
            logger.error('commits field does not decode to dict')
            return INVALID_FORM_DATA, {'fields': {'commits': 'Does not decode to a dict'}}

        for key in ('squashed', 'individual'):
            if key not in commits:
                logger.error('commits field does not contain %s' % key)
                return INVALID_FORM_DATA, {
                    'fields': {'commits': 'Does not contain %s key' % key}}

        for key in ('base_commit_id', 'diff', 'first_public_ancestor'):
            if key not in commits['squashed']:
                logger.error('squashed key missing %s' % key)
                return INVALID_FORM_DATA, {
                    'fields': {
                        'commits': 'Squashed commit does not contain %s key' % key}}

        # TODO validate individual commits.

        try:
            repo = Repository.objects.get(pk=int(repo_id), local_site=local_site)
        except ValueError:
            logger.warn('repo_id not an integer: %s' % repo_id)
            return INVALID_FORM_DATA, {'fields': {'repo_id': 'Not an integer'}}
        except Repository.DoesNotExist:
            logger.warn('repo %d does not exist' % repo_id)
            return INVALID_FORM_DATA, {'fields': {'repo_id': 'Invalid repo_id'}}

        if not repo.is_accessible_by(user):
            return self.get_no_access_error(request)

        try:
            with transaction.atomic():
                squashed_rr = self._process_submission(
                    request, local_site, repo, identifier, commits)

                return 200, {
                    self.item_result_key: {
                        'squashed_rr': squashed_rr.id,
                    }
                }

        # Need to catch this outside the transaction so db changes are rolled back.
        except DiffProcessingException:
            return INVALID_FORM_DATA, {
                'fields': {'commits': 'error processing squashed diff'}}

    def _process_submission(self, request, local_site, repo, identifier, commits):
        user = request.user
        try:
            squashed_rr = ReviewRequest.objects.get(commit_id=identifier,
                                                    repository=repo)
            if not squashed_rr.is_mutable_by(user):
                logger.warn('%s not mutable by %s' % (squashed_rr.id, user))
                return self.get_no_access_error(request)

            if squashed_rr.status != ReviewRequest.PENDING_REVIEW:
                logger.warn('%s is not a pending review request; cannot edit' %
                            squashed_rr.id)
                return INVALID_FORM_DATA, {
                    'fields': {'identifier': 'Parent review request is '
                               'submitted or discarded'}}

        except ReviewRequest.DoesNotExist:
            squashed_rr = ReviewRequest.objects.create(
                    user=user, repository=repo, commit_id=identifier,
                    local_site=local_site)

            squashed_rr.extra_data.update({
                'p2rb': True,
                'p2rb.is_squashed': True,
                'p2rb.identifier': identifier,
                'p2rb.discard_on_publish_rids': '[]',
                'p2rb.unpublished_rids': '[]',
                'p2rb.first_public_ancestor': commits['squashed']['first_public_ancestor'],
            })
            squashed_rr.save(update_fields=['extra_data'])
            logger.info('created squashed review request #%d' % squashed_rr.id)

        # The diffs on diffsets can't be updated, only replaced. So always
        # construct the diffset.

        try:
            # TODO consider moving diffset creation outside of the transaction
            # since it can be quite time consuming.
            # Calling create_from_data() instead of create_from_upload() skips
            # diff size validation. We allow unlimited diff sizes, so no biggie.
            diffset = DiffSet.objects.create_from_data(
                repository=repo,
                diff_file_name='diff',
                diff_file_contents=commits['squashed']['diff'],
                parent_diff_file_name=None,
                parent_diff_file_contents=None,
                diffset_history=None,
                basedir='',
                request=request,
                base_commit_id=commits['squashed'].get('base_commit_id'),
                save=True,
                )

            update_diffset_history(squashed_rr, diffset)
            diffset.save()

        except Exception:
            logger.exception('error processing squashed diff')
            raise DiffProcessingException()

        update_review_request_draft_diffset(squashed_rr, diffset)

        return squashed_rr

batch_review_request_resource = BatchReviewRequestResource()


def update_diffset_history(rr, diffset):
    """Update the diffset revision from a review request.

    This should be called when creating new DiffSet so that the new item
    is linked to the old.

    Callers must call ``diffset.save()`` afterwards for changes to be preserved.
    This is because other changes are typically performed when this function
    is called.
    """
    public_diffsets = rr.diffset_history.diffsets
    try:
        latest_diffset = public_diffsets.latest()
        diffset.revision = latest_diffset.revision + 1
    except DiffSet.DoesNotExist:
        diffset.revision = 1


def update_review_request_draft_diffset(rr, diffset):
    """Update the diffset on a review request draft.

    Given a ReviewRequest, obtain or create the draft and update the diffset
    on it.
    """
    discarded_diffset = None

    try:
        draft = rr.draft.get()
        if draft.diffset and draft.diffset != diffset:
            discarded_diffset = draft.diffset
    except ReviewRequestDraft.DoesNotExist:
        draft = ReviewRequestDraft.create(rr)

    draft.diffset = diffset
    draft.save()

    if discarded_diffset:
        discarded_diffset.delete()

    return draft
