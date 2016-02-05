from __future__ import absolute_import, unicode_literals

import json
import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from djblets.webapi.decorators import (
    webapi_login_required,
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.webapi.errors import (
    INVALID_FORM_DATA,
    LOGIN_FAILED,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
    SERVICE_NOT_CONFIGURED,
)
from reviewboard.accounts.backends import (
    get_enabled_auth_backends,
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
from reviewboard.webapi.encoder import (
    status_to_string,
)
from reviewboard.webapi.resources import (
    WebAPIResource,
)

from mozreview.extra_data import (
    BASE_COMMIT_KEY,
    COMMITS_KEY,
    COMMIT_ID_KEY,
    DISCARD_ON_PUBLISH_KEY,
    fetch_commit_data,
    FIRST_PUBLIC_ANCESTOR_KEY,
    IDENTIFIER_KEY,
    MOZREVIEW_KEY,
    SQUASHED_KEY,
    UNPUBLISHED_KEY,
)
from mozreview.models import (
    DiffSetVerification,
)
from mozreview.resources.bugzilla_login import (
    auth_api_key
)
from mozreview.review_helpers import (
    gen_latest_reviews,
)

logger = logging.getLogger(__name__)


class DiffProcessingException(Exception):
    pass


class SubmissionException(Exception):
    def __init__(self, value):
        self.value = value


class BatchReviewRequestResource(WebAPIResource):
    """Resource for creating a series of review requests with a single request.

    Submitting multiple review requests using the traditional Web API requires
    several HTTP requests and the count grows in proportion to the number of
    review requests being submitted. In addition, changes are only atomic
    within each HTTP request. This API exists to make submitting a review
    series a single HTTP request while also being atomic.

    Each commit will become its own review request.
    Additionally, a review request with a diff encompassing all the commits
    will be created; This "squashed" review request will represent the push
    for the provided ``identifier``.

    The ``identifier`` is a unique string which represents a series of pushed
    commit sets. This identifier is used to update review requests with a new
    set of diffs from a new push. Generally this identifier will represent
    some unit of work, such as a bug.

    The ``commits`` argument takes the following form::

        {
            'squashed': {
                'diff': <squashed-diff-string>,
                'base_commit_id': <commit-id-to-apply-diff-to> (optional),
                'first_public_ancestor': <commit of first public ancestor> (optional),
            },
            'individual': [
                {
                    'id': <commit-id>,
                    'precursors': [<previous changeset>],
                    'message': <commit-message>,
                    'diff': <diff>,
                    'bug': <bug-id>,
                    'parent_diff': <diff-from-base-to-commit> (optional),
                    'base_commit_id': <commit-id-to-apply-diffs-to> (optional),
                    'first_public_ancestor': <commit of first public ancestor> (optional),
                    'reviewers': [<user1>, <user2>, ...] (optional),
                    'requal_reviewers': [<user1>, <user2>, ...] (optional),
                },
                {
                    ...
                },
                ...
            ]
        }

    When representing the commits on Review Board, we store meta data in the
    extra_data dictionaries. We use a number of fields to keep track of review
    requests and the state they are in.

    The following ASCII Venn Diagram represents sets the related review requests
    may be in and how they overlap.

    Legend:

    * "unpublished_rids" = squashed_rr.extra_data['p2rb.unpublished_rids']
    * "discard_on_publish_rids" = squashed_rr.extra_data['p2rb.discard_on_publish_rids']
    * "squashed.commits" = squashed_rr.extra_data['p2rb.commits']
    * "draft.commits" = squashed_rr.draft.extra_data['p2rb.commits']

    * A = unpublished_rids - draft.commits
    * B = draft.commits - squashed.commits
    * C = draft.commits - unpublished rids
    * D = delete_on_publish_rids

    Diagram::

                unpublished_rids                       squashed.commits
         ________________________________________________________________
        |                             |                                  |
        |                             |                                  |
        |                _____________|_____________                     |
        |               |             |             |                    |
        |        A      |       draft.commits       |           D        |
        |               |             |             |                    |
        |               |             |             |                    |
        |               |      B      |        C    |                    |
        |               |             |             |                    |
        |               |             |             |                    |
        |               |_____________|_____________|                    |
        |                             |                                  |
        |                             |         discard_on_publish_rids  |
        |                             |                                  |
        |_____________________________|__________________________________|


    The following rules should apply to the review request sets when publishing
    or discarding.

    When publishing the squashed review request:

    * A: close "discarded" because it was never used
    * B: publish draft
    * C: publish draft
    * D: close "discarded" because it is obsolete
    * set unpublished_rids to empty '[]'
    * set discard_on_publish_rids to empty '[]'

    When discarding the draft of a published squashed review request:

    * A: close "discarded" because it was never used (so it does not appear in
      the owners dashboard)
    * B: close "discarded" because it was never used (so it does not appear in
      the owners dashboard)
    * C: DELETE the review request draft
    * D: do nothing
    * set unpublished_rids to empty '[]'
    * set discard_on_publish_rids to empty '[]'

    When discarding an unpublished squashed review request (always a close "discarded"):
    """
    name = 'batch_review_request'
    allowed_methods = ('GET', 'POST',)

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(
        INVALID_FORM_DATA,
        LOGIN_FAILED,
        NOT_LOGGED_IN,
        PERMISSION_DENIED,
        SERVICE_NOT_CONFIGURED,
    )
    @webapi_request_fields(
        required={
            'username': {
                'type': str,
                'description': 'Bugzilla username/email',
            },
            'api_key': {
                'type': str,
                'description': 'Bugzilla API key',
            },
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
    def create(self, request, username, api_key, repo_id, identifier, commits,
               local_site_name=None, **kwargs):
        """Create or update a review request series."""
        if not request.user.has_perm('mozreview.verify_diffset'):
            return PERMISSION_DENIED

        # The requesting user has the `verify_diffset` permission
        # indicating they are a privileged user and allowed to access
        # this resource.
        privileged_user = request.user

        # Now check the provided Bugzilla credentials to authenticate
        # the user the privileged_user is speaking on behalf of.
        result = auth_api_key(request, username, api_key)

        if not isinstance(result, User):
            return result

        # Now that we've confirmed permissions and credentials we will
        # spoof the authenticated User in the request object. This
        # prevents us from accidentally carrying out any operations
        # as the special privileged User and means we don't need to
        # change any of the AuthBackend code that relies on request.user
        # for contacting Bugzilla. We'll also flush the session to make
        # sure nothing is hanging around there from the privileged User.
        user = result
        request.user = user
        request.session.flush()

        local_site = self._get_local_site(local_site_name)
        logger.info('processing BatchReviewRequest for %s' % user)

        try:
            commits = json.loads(commits)
        except ValueError:
            logger.error('invalid JSON in commits field')
            return INVALID_FORM_DATA, {
                'fields': {
                    'commits': ['Not valid JSON.']}}

        if not isinstance(commits, dict):
            logger.error('commits field does not decode to dict')
            return INVALID_FORM_DATA, {
                'fields': {
                    'commits': ['Does not decode to a dict']}}

        for key in ('squashed', 'individual'):
            if key not in commits:
                logger.error('commits field does not contain %s' % key)
                return INVALID_FORM_DATA, {
                    'fields': {
                        'commits': ['Does not contain %s key' % key]}}

        for key in ('base_commit_id', 'diff', 'first_public_ancestor'):
            if key not in commits['squashed']:
                logger.error('squashed key missing %s' % key)
                return INVALID_FORM_DATA, {
                    'fields': {
                        'commits': ['Squashed commit does not contain %s key' % key]}}

        for commit in commits['individual']:
            for key in ('id', 'message', 'bug', 'diff', 'precursors', 'first_public_ancestor'):
                if key not in commit:
                    logger.error('commit (%s) missing key %s' % (
                                 commit.get('id', '<id>') ,key))
                    return INVALID_FORM_DATA, {
                        'fields': {
                            'commits': ['Individual commit (%s) missing key %s' % (
                                commit.get('id', '<id>'), key)]
                        }}

        try:
            repo = Repository.objects.get(pk=int(repo_id), local_site=local_site)
        except ValueError:
            logger.warn('repo_id not an integer: %s' % repo_id)
            return INVALID_FORM_DATA, {
                'fields': {
                    'repo_id': ['Not an integer']}}
        except Repository.DoesNotExist:
            logger.warn('repo %d does not exist' % repo_id)
            return INVALID_FORM_DATA, {
                'fields': {
                    'repo_id': ['Invalid repo_id']}}

        if not repo.is_accessible_by(user):
            logger.warn('repo %s not accessible by %s' % (repo.id, user))
            return self.get_no_access_error(request)

        try:
            with transaction.atomic():
                res = self._process_submission(
                    request, local_site, user, privileged_user, repo,
                    identifier, commits)

                squashed_rr, node_to_rid, review_data, warnings = res

                logger.info('%s: finished processing %d' % (
                            identifier, squashed_rr.id))

                return 200, {
                    self.item_result_key: {
                        'nodes': node_to_rid,
                        'squashed_rr': squashed_rr.id,
                        'review_requests': review_data,
                        'warnings': warnings,
                    }}

        # Need to catch outside the transaction so db changes are rolled back.
        except DiffProcessingException:
            logging.exception('diff processing exception')
            return INVALID_FORM_DATA, {
                'fields': {
                    'commits': ['error processing squashed diff']}}
        except SubmissionException as e:
            logging.exception('submission exception')
            return e.value

    def _process_submission(self, request, local_site, user, privileged_user,
                            repo, identifier, commits):
        logger.info('processing batch submission %s to %s with %d commits' % (
                    identifier, repo.name, len(commits)))

        try:
            squashed_rr = ReviewRequest.objects.get(commit_id=identifier,
                                                    repository=repo)
            if not squashed_rr.is_mutable_by(user):
                logger.warn('%s not mutable by %s' % (squashed_rr.id, user))
                raise SubmissionException(self.get_no_access_error(request))

            if squashed_rr.status != ReviewRequest.PENDING_REVIEW:
                logger.warn('%s is not a pending review request; cannot edit' %
                            squashed_rr.id)
                raise SubmissionException((INVALID_FORM_DATA, {
                    'fields': {
                        'identifier': ['Parent review request is '
                               'submitted or discarded']}}))

            logger.info('using squashed review request %d' % squashed_rr.id)

        except ReviewRequest.DoesNotExist:
            squashed_rr = ReviewRequest.objects.create(
                    user=user, repository=repo, commit_id=identifier,
                    local_site=local_site)

            squashed_commit_data = fetch_commit_data(squashed_rr)
            squashed_commit_data.extra_data.update({
                IDENTIFIER_KEY: identifier,
                FIRST_PUBLIC_ANCESTOR_KEY: (
                    commits['squashed']['first_public_ancestor']),
                SQUASHED_KEY: True,
                DISCARD_ON_PUBLISH_KEY: '[]',
                UNPUBLISHED_KEY: '[]',
            })
            squashed_commit_data.draft_extra_data.update({
                IDENTIFIER_KEY: identifier,
            })
            squashed_commit_data.save(
                update_fields=['extra_data', 'draft_extra_data'])

            squashed_rr.extra_data.update({
                MOZREVIEW_KEY: True,
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
            logger.info('%s: generating squashed diffset for %d' % (
                        identifier, squashed_rr.id))
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

            # We pass `force_insert=True` to save to make sure Django generates
            # an SQL INSERT rather than an UPDATE if the DiffSetVerification
            # already exists. It should never already exist so we want the
            # exception `force_insert=True` will cause if that's the case.
            DiffSetVerification(diffset=diffset).save(
                authorized_user=privileged_user, force_insert=True)
        except Exception:
            logger.exception('error processing squashed diff')
            raise DiffProcessingException()

        update_review_request_draft_diffset(squashed_rr, diffset)
        logger.info('%s: updated squashed diffset for %d' % (
                    identifier, squashed_rr.id))

        # TODO: We need to take into account the commits data from the squashed
        # review request's draft. This data represents the mapping from commit
        # to rid in the event that we would have published. We're overwritting
        # this data. This will only come into play if we start trusting the server
        # instead of the client when matching review request ids. Bug 1047516

        squashed_commit_data = fetch_commit_data(squashed_rr)
        previous_commits = get_previous_commits(squashed_rr,
                                                squashed_commit_data)
        remaining_nodes = get_remaining_nodes(previous_commits)
        discard_on_publish_rids = get_discard_on_publish_rids(
            squashed_rr, squashed_commit_data)
        unpublished_rids = get_unpublished_rids(
            squashed_rr, squashed_commit_data)
        unclaimed_rids = get_unclaimed_rids(previous_commits,
                                            discard_on_publish_rids,
                                            unpublished_rids)

        logger.info('%s: %d previous commits; %d discard on publish; '
                    '%d unpublished' % (identifier, len(previous_commits),
                                        len(discard_on_publish_rids),
                                        len(unpublished_rids)))

        # Previously pushed nodes which have been processed and had their review
        # request updated or did not require updating.
        processed_nodes = set()

        node_to_rid = {}

        # A mapping from review request id to the corresponding ReviewRequest.
        review_requests = {}

        # A mapping of review request id to dicts of additional metadata.
        review_data = {}

        squashed_reviewers = set()
        reviewer_cache = ReviewerCache(request)

        warnings = []

        # Do a pass and find all commits that map cleanly to old review requests.
        for commit in commits['individual']:
            node = commit['id']

            if node not in remaining_nodes:
                continue

            # If the commit appears in an old review request, by definition of
            # commits deriving from content, the commit has not changed and there
            # is nothing to update. Update our accounting and move on.
            rid = remaining_nodes[node]
            logger.info('%s: commit %s unchanged; using existing request %d' % (
                        identifier, node, rid))

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

        logger.info('%s: %d/%d commits mapped exactly' % (
                    identifier, len(processed_nodes),
                    len(commits['individual'])))

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

                logger.info('%s: found precursor to commit %s; '
                            'using existing review request %d' % (
                            identifier, node, rid))

                del remaining_nodes[precursor]
                unclaimed_rids.remove(rid)

                rr = ReviewRequest.objects.get(pk=rid)
                draft, warns = update_review_request(local_site, request,
                                                     privileged_user,
                                                     reviewer_cache, rr,
                                                     commit)
                squashed_reviewers.update(u for u in draft.target_people.all())
                warnings.extend(warns)
                processed_nodes.add(node)
                node_to_rid[node] = rid
                review_requests[rid] = rr
                review_data[rid] = get_review_request_data(rr)

                try:
                    discard_on_publish_rids.remove(rid)
                except ValueError:
                    pass

                break

        logger.info('%s: %d/%d mapped exactly or to precursors' % (
                    identifier, len(processed_nodes),
                    len(commits['individual'])))

        # Now do a pass over the commits that didn't map cleanly.
        for commit in commits['individual']:
            node = commit['id']
            if node in processed_nodes:
                continue

            # We haven't seen this commit before *and* our mapping above didn't
            # do anything useful with it.

            # This is where things could get complicated. We could involve
            # heuristic based matching (comparing commit messages, changed
            # files, etc). We may do that in the future.

            # For now, match the commit up against the next one in the index.
            # The unclaimed rids list contains review requests which were created
            # when previously updating this review identifier, but not published.
            # If we have more commits than were previously published we'll start
            # reusing these private review requests before creating new ones.
            if unclaimed_rids:
                assumed_old_rid = unclaimed_rids.pop(0)

                logger.info('%s: mapping %s to unclaimed request %d' % (
                            identifier, node, assumed_old_rid))

                rr = ReviewRequest.objects.get(pk=assumed_old_rid)
                draft, warns = update_review_request(local_site, request,
                                                     privileged_user,
                                                     reviewer_cache, rr,
                                                     commit)
                squashed_reviewers.update(u for u in draft.target_people.all())
                warnings.extend(warns)
                processed_nodes.add(commit['id'])
                node_to_rid[node] = assumed_old_rid
                review_requests[assumed_old_rid] = rr
                review_data[assumed_old_rid] = get_review_request_data(rr)

                try:
                    discard_on_publish_rids.remove(assumed_old_rid)
                except ValueError:
                    pass

                continue

            # There are no more unclaimed review request IDs. This means we have
            # more commits than before. Create new review requests as appropriate.
            rr = ReviewRequest.objects.create(user=user,
                                              repository=repo,
                                              commit_id=None,
                                              local_site=local_site)

            commit_data = fetch_commit_data(rr)
            commit_data.extra_data.update({
                IDENTIFIER_KEY: identifier,
                SQUASHED_KEY: False,
            })
            commit_data.draft_extra_data.update({
                IDENTIFIER_KEY: identifier,
            })
            commit_data.save(
                update_fields=['extra_data', 'draft_extra_data'])

            rr.extra_data[MOZREVIEW_KEY] = True
            rr.save(update_fields=['extra_data'])
            logger.info('%s: created review request %d for commit %s' % (
                        identifier, rr.id, node))
            draft, warns = update_review_request(local_site, request,
                                                 privileged_user,
                                                 reviewer_cache, rr, commit)
            squashed_reviewers.update(u for u in draft.target_people.all())
            warnings.extend(warns)
            processed_nodes.add(commit['id'])
            node_to_rid[node] = rr.id
            review_requests[rr.id] = rr
            review_data[rr.id] = get_review_request_data(rr)
            unpublished_rids.append(rr.id)

        # At this point every incoming commit has been accounted for.
        # If there are any remaining review requests, they must belong to
        # deleted commits. (Or, we made a mistake and updated the wrong review
        # request)
        logger.info('%s: %d unclaimed review requests left over' % (
                    identifier, len(unclaimed_rids)))
        for rid in unclaimed_rids:
            rr = ReviewRequest.objects.get(pk=rid)

            if rr.public and rid not in discard_on_publish_rids:
                # This review request has already been published so we'll need to
                # discard it when we publish the squashed review request.
                discard_on_publish_rids.append(rid)
            elif not rr.public and rid not in unpublished_rids:
                # We've never published this review request so it may be reused in
                # the future for *any* commit. Keep track of it.
                unpublished_rids.append(rid)
            else:
                # This means we've already marked the review request properly
                # in a previous push, so do nothing.
                pass

        commit_list = []
        for commit in commits['individual']:
            node = commit['id']
            commit_list.append([node, node_to_rid[node]])

        # We need to refresh the squashed rr and draft because post save hooks
        # in ReviewBoard result in magical changes to some of its fields.
        squashed_rr = ReviewRequest.objects.get(pk=squashed_rr.id)
        squashed_draft = squashed_rr.draft.get()
        squashed_commit_data = fetch_commit_data(squashed_rr)

        squashed_draft.summary = identifier

        # Reviewboard does not allow review requests with empty descriptions to
        # be published, so we insert some filler here.
        squashed_draft.description = 'This is the parent review request'
        squashed_draft.bugs_closed = ','.join(sorted(set(commit['bug'] for commit in commits['individual'])))

        squashed_draft.depends_on.clear()
        for rrid in sorted(node_to_rid.values()):
            rr = ReviewRequest.objects.for_id(rrid, local_site)
            squashed_draft.depends_on.add(rr)

        squashed_draft.target_people.clear()
        for user in sorted(squashed_reviewers):
            squashed_draft.target_people.add(user)

        squashed_commit_data.draft_extra_data[COMMITS_KEY] = json.dumps(
            commit_list)

        if 'base_commit_id' in commits['squashed']:
            squashed_commit_data.draft_extra_data[BASE_COMMIT_KEY] = (
                commits['squashed']['base_commit_id'])

        squashed_commit_data.extra_data.update({
            DISCARD_ON_PUBLISH_KEY: json.dumps(discard_on_publish_rids),
            FIRST_PUBLIC_ANCESTOR_KEY: (
                commits['squashed']['first_public_ancestor']),
            UNPUBLISHED_KEY: json.dumps(unpublished_rids),
        })

        squashed_draft.save()
        squashed_rr.save(update_fields=['extra_data'])
        squashed_commit_data.save(
            update_fields=['extra_data', 'draft_extra_data'])

        review_requests[squashed_rr.id] = squashed_rr
        review_data[squashed_rr.id] = get_review_request_data(squashed_rr)

        return squashed_rr, node_to_rid, review_data, warnings


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


def update_review_request_draft_diffset(rr, diffset, draft=None):
    """Update the diffset on a review request draft.

    Given a ReviewRequest, obtain or create the draft and update the diffset
    on it.
    """
    if not draft:
        try:
            draft = rr.draft.get()
        except ReviewRequestDraft.DoesNotExist:
            draft = ReviewRequestDraft.create(rr)

    discarded_diffset = None

    if draft.diffset and draft.diffset != diffset:
        discarded_diffset = draft.diffset

    draft.diffset = diffset

    # Only add default reviewers if this is the first time a diffset has
    # been added.
    if rr.diffset_history.diffsets.count() == 0:
        draft.add_default_reviewers()

    draft.save()

    if discarded_diffset:
        # We need to delete the DiffSetVerification manually because
        # we can't rely on the model relationship from a built-in model
        # to our extension's model.
        try:
            DiffSetVerification.objects.get(diffset=discarded_diffset).delete()
        except DiffSetVerification.DoesNotExist:
            logger.error('A DiffSetVerification did not exist when cleaning '
                         'up a draft DiffSet for review request %i' % rr.id)

        discarded_diffset.delete()

    return draft


def previous_reviewers(rr):
    """Return the result of the most recent review given by each reviewer"""

    # TODO: Ideally this would get approval state for each reviewer as
    # calculated in the MozReviewApprovalHook to be absolutely sure we're
    # consistent.
    pr = {}
    for review in gen_latest_reviews(rr):
        pr[review.user.username] = review.ship_it

    return pr


class ReviewerCache(object):
    """Caches lookups from reviewer/username to User instances.

    Resolving a username string to a User potentially requires querying
    Bugzilla via an HTTP request. To minimize the number of HTTP requests,
    we cache lookups.
    """

    def __init__(self, request):
        self._request = request
        self._d = {}

    def resolve_reviewer(self, reviewer):
        """Try to obtain a User for a reviewer.

        Returns None if the reviewer/user is unknown.
        """
        if reviewer not in self._d:
            self._d[reviewer] = get_user_from_reviewer(self._request, reviewer)

        return self._d[reviewer]


def get_user_from_reviewer(request, reviewer):
    for backend in get_enabled_auth_backends():
        backend.query_users(reviewer, request)

    q = Q(username__icontains=reviewer)
    q = q | Q(is_active=True)

    users = User.objects.filter(q).all()
    # Try exact username match.
    for user in users:
        if user.username == reviewer:
            return user

    # Try case insensitive username match.
    for user in users:
        if user.username.lower() == reviewer.lower():
            return user

    return None


def resolve_reviewers(cache, requested_reviewers):
    reviewers = set()
    unrecognized = set()
    # TODO track mapping for multiple review requests and cache results.
    for reviewer in requested_reviewers:
        user = cache.resolve_reviewer(reviewer)
        if user:
            if not any(u.username == user.username for u in reviewers):
                reviewers.add(user)
        else:
            unrecognized.add(reviewer)

    return reviewers, unrecognized


def update_review_request(local_site, request, privileged_user, reviewer_cache,
                          rr, commit):
    """Synchronize the state of a review request with a commit.

    Updates the commit message, refreshes the diff, etc.
    """
    try:
        draft = rr.draft.get()
    except ReviewRequestDraft.DoesNotExist:
        draft = ReviewRequestDraft.create(rr)

    draft.summary = commit['message'].splitlines()[0]
    draft.description = commit['message']
    draft.bugs_closed = commit['bug']

    commit_data = fetch_commit_data(draft)
    commit_data.draft_extra_data.update({
        COMMIT_ID_KEY: commit['id'],
        FIRST_PUBLIC_ANCESTOR_KEY: commit['first_public_ancestor'],
    })
    commit_data.save(
        update_fields=['draft_extra_data'])

    reviewer_users, unrecognized_reviewers = \
        resolve_reviewers(reviewer_cache, commit.get('reviewers', []))
    requal_reviewer_users, unrecognized_requal_reviewers = \
        resolve_reviewers(reviewer_cache, commit.get('requal_reviewers', []))

    warnings = []

    for reviewer in unrecognized_reviewers | unrecognized_requal_reviewers:
        warnings.append('unrecognized reviewer: %s' % reviewer)
        logger.info('unrecognized reviewer: %s' % reviewer)

    if requal_reviewer_users:
        pr = previous_reviewers(rr)
        for user in requal_reviewer_users:
            if not pr.get(user.username, False):
                warnings.append('commit message for %s has r=%s but they '
                                'have not granted a ship-it. review will be '
                                'requested on your behalf' % (
                                commit['id'][:12], user.username))

        reviewer_users |= requal_reviewer_users

    # Carry over from last time unless commit message overrules.
    if reviewer_users:
        draft.target_people.clear()
    for user in sorted(reviewer_users):
        draft.target_people.add(user)
        logger.debug('adding reviewer %s to #%d' % (user.username, rr.id))

    try:
        diffset = DiffSet.objects.create_from_data(
            repository=rr.repository,
            diff_file_name='diff',
            diff_file_contents=commit['diff'],
            parent_diff_file_name='diff',
            parent_diff_file_contents=commit.get('parent_diff'),
            diffset_history=None,
            basedir='',
            request=request,
            base_commit_id=commit.get('base_commit_id'),
            save=True,
        )
        update_diffset_history(rr, diffset)
        diffset.save()

        DiffSetVerification(diffset=diffset).save(
            authorized_user=privileged_user, force_insert=True)
    except Exception:
        logger.exeption('error processing diff')
        raise DiffProcessingException()

    update_review_request_draft_diffset(rr, diffset, draft=draft)

    return draft, warnings


def get_review_request_data(rr):
    """Obtain a dictionary containing review request metadata.

    The dict consists of plain types (as opposed to ReviewBoard types).

    Some values may be unicode, not str.
    """
    rd = {
        'status': status_to_string(rr.status),
    }

    thing = rr
    try:
        thing = rr.draft.get()
        rd['public'] = False
    except ReviewRequestDraft.DoesNotExist:
        rd['public'] = rr.public

    rd['reviewers'] = [p.username for p in thing.target_people.all()]

    return rd


def get_previous_commits(squashed_rr, commit_data=None):
    """Retrieve the previous commits from a squashed review request.

    This will return a list of tuples specifying the previous commit
    id as well as the review request it is represented by. ex::

        [
            # (<commit-id>, <review-request-id>),
            ('d4bd89322f54', 13),
            ('373537353134', 14),
        ]
    """
    commit_data = fetch_commit_data(squashed_rr, commit_data)

    if not squashed_rr.public:
        extra_data = commit_data.draft_extra_data
    else:
        extra_data = commit_data.extra_data

    if COMMITS_KEY not in extra_data:
        return []

    commits = []
    for node, rid in json.loads(extra_data[COMMITS_KEY]):
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


def get_discard_on_publish_rids(squashed_rr, commit_data=None):
    """A list of review request ids that should be discarded when publishing.
    Adding to this list will mark a review request as to-be-discarded when
    the squashed draft is published on Review Board.
    """
    commit_data = fetch_commit_data(squashed_rr, commit_data)
    return map(int, json.loads(
               commit_data.extra_data[DISCARD_ON_PUBLISH_KEY]))


def get_unpublished_rids(squashed_rr, commit_data=None):
    """A list of review request ids that have been created for individual commits
    but have not been published. If this list contains an item, it should be
    re-used for indiviual commits instead of creating a brand new review
    request.
    """
    commit_data = fetch_commit_data(squashed_rr, commit_data)
    return map(int, json.loads(commit_data.extra_data[UNPUBLISHED_KEY]))


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
