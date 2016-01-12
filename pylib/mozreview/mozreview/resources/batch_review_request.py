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

        for commit in commits['individual']:
            for key in ('id', 'message', 'bug', 'diff', 'precursors', 'first_public_ancestor'):
                if key not in commit:
                    logger.error('commit (%s) missing key %s' % (
                                 commit.get('id', '<id>') ,key))
                    return INVALID_FORM_DATA, {
                        'fields': {
                            'commits': 'Individual commit (%s) missing key %s' % (
                                commit.get('id', '<id>'), key)
                        }}

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

        # TODO: We need to take into account the commits data from the squashed
        # review request's draft. This data represents the mapping from commit
        # to rid in the event that we would have published. We're overwritting
        # this data. This will only come into play if we start trusting the server
        # instead of the client when matching review request ids. Bug 1047516

        previous_commits = get_previous_commits(squashed_rr)
        remaining_nodes = get_remaining_nodes(previous_commits)
        discard_on_publish_rids = get_discard_on_publish_rids(squashed_rr)
        unpublished_rids = get_unpublished_rids(squashed_rr)
        unclaimed_rids = get_unclaimed_rids(previous_commits,
                                            discard_on_publish_rids,
                                            unpublished_rids)

        # Previously pushed nodes which have been processed and had their review
        # request updated or did not require updating.
        processed_nodes = set()

        node_to_rid = {}

        # A mapping from review request id to the corresponding ReviewRequest.
        review_requests = {}

        # A mapping of review request id to dicts of additional metadata.
        review_data = {}

        # Do a pass and find all commits that map cleanly to old review requests.
        for commit in commits['individual']:
            node = commit['id']

            if node not in remaining_nodes:
                continue

            # If the commit appears in an old review request, by definition of
            # commits deriving from content, the commit has not changed and there
            # is nothing to update. Update our accounting and move on.
            rid = remaining_nodes[node]
            del remaining_nodes[node]
            unclaimed_rids.remove(rid)
            processed_nodes.add(node)
            node_to_rid[node] = rid

            rr = ReviewRequest.objects.get(pk=rid)
            review_requests[rid] = rr
            review_data[rid] = get_review_request_data(rr)

            try:
                discard_on_publish_rids.remove(rid)
            except ValueError:
                pass

        # Find commits that map to a previous version.
        for commit in commits['individual']:
            node = commit['id']
            if node in processed_nodes:
                continue

            # The client may have sent obsolescence data saying which commit this
            # commit has derived from. Use that data (if available) to try to find
            # a mapping to an old review request.
            for precursor in commit['precursors']:
                rid = remaining_nodes.get(precursor)
                if not rid:
                    continue

                del remaining_nodes[precursor]
                unclaimed_rids.remove(rid)

                rr = ReviewRequest.objects.get(pk=rid)
                # TODO implement
                #update_review_request(rr, commit)
                processed_nodes.add(node)
                node_to_rid[node] = rid
                review_requests[rid] = rr
                review_data[rid] = get_review_request_data(rr)

                try:
                    discard_on_publish_rids.remove(rid)
                except ValueError:
                    pass

                break

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


def get_review_request_data(rr):
    """Obtain a dictionary containing review request metadata.

    The dict consists of plain types (as opposed to ReviewBoard types).

    Some values may be unicode, not str.
    """
    rd = {
        'status': rr.status,
    }

    thing = rr
    try:
        thing = rr.draft.get()
        rd['public'] = False
    except ReviewRequestDraft.DoesNotExist:
        rd['public'] = rr.public

    rd['reviewers'] = [p.username for p in thing.target_people.all()]

    return rd


def get_previous_commits(squashed_rr):
    """Retrieve the previous commits from a squashed review request.

    This will return a list of tuples specifying the previous commit
    id as well as the review request it is represented by. ex::

        [
            # (<commit-id>, <review-request-id>),
            ('d4bd89322f54', 13),
            ('373537353134', 14),
        ]
    """
    if not squashed_rr.public:
        extra_data = squashed_rr.get_draft().extra_data
    else:
        extra_data = squashed_rr.extra_data

    if 'p2rb.commits' not in extra_data:
        return []

    commits = []
    for node, rid in json.loads(extra_data['p2rb.commits']):
        # JSON decoding likes to give us unicode types. We speak str
        # internally, so convert.
        if isinstance(node, unicode):
            node = node.encode('utf-8')

        assert isinstance(node, str)

        commits.append((node, int(rid)))

    return commits


def get_remaining_nodes(previous_commits):
    """A mapping from previously pushed node, which has not been processed
    yet, to the review request id associated with that node.
    """
    return dict((t[0], t[1]) for i, t in enumerate(previous_commits))


def get_discard_on_publish_rids(squashed_rr):
    """A list of review request ids that should be discarded when publishing.
    Adding to this list will mark a review request as to-be-discarded when
    the squashed draft is published on Review Board.
    """
    return map(int, json.loads(
               squashed_rr.extra_data['p2rb.discard_on_publish_rids']))


def get_unpublished_rids(squashed_rr):
    """A list of review request ids that have been created for individual commits
    but have not been published. If this list contains an item, it should be
    re-used for indiviual commits instead of creating a brand new review
    request.
    """
    return map(int, json.loads(
               squashed_rr.extra_data['p2rb.unpublished_rids']))


def get_unclaimed_rids(previous_commits, discard_on_publish_rids,
                       unpublished_rids):
    """Set of review request ids which have not been matched to a commit
    from the current push. We use a list to represent this set because
    if any entries are left over we need to process them in order.
    This list includes currently published rids that were part of the
    previous push and rids which have been used for drafts on this
    reviewid but have not been published.
    """
    unclaimed_rids = [t[1] for t in previous_commits]

    for rid in (discard_on_publish_rids + unpublished_rids):
        if rid not in unclaimed_rids:
            unclaimed_rids.append(rid)

    return unclaimed_rids
