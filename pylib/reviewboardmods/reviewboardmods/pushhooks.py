"""Push commits to Review Board.

This module contains code for taking commits from version control (Git,
Mercurial, etc) and adding them to Review Board.

It is intended for this module to be generic and applicable to any
Review Board install. Please abstract away Mozilla implementation
details.
"""

from contextlib import contextmanager
import os
import json
import tempfile

from rbtools.api.client import RBClient
from rbtools.api.errors import APIError
from rbtools.api.transport.sync import SyncTransport


def post_reviews(url, repoid, identifier, commits, hgresp,
                 username=None, password=None, userid=None, cookie=None):
    """Post a set of commits to Review Board.

    Repository hooks can use this function to post a set of pushed commits
    to Review Board. Each commit will become its own review request.
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
            },
            'individual': [
                {
                    'id': <commit-id>,
                    'precursors': [<previous changeset>],
                    'message': <commit-message>,
                    'diff': <diff>,
                    'parent_diff': <diff-from-base-to-commit> (optional),
                    'base_commit_id': <commit-id-to-apply-diffs-to> (optional),
                    'reviewers': [<user1>, <user2>, ...] (optional),
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

    * TODO Bug 1047465
    """
    with ReviewBoardClient(url, username, password, userid, cookie) as rbc:
        root = rbc.get_root()
        return _post_reviews(root, repoid, identifier, commits, hgresp)

def _post_reviews(api_root, repoid, identifier, commits, hgresp):
    # This assumes that we pushed to the repository/URL that Review Board is
    # configured to use. This assumption may not always hold.
    repo = api_root.get_repository(repository_id=repoid)
    repo_url = repo.path

    # Retrieve the squashed review request or create it.
    previous_commits = []
    squashed_rr = None
    rrs = api_root.get_review_requests(commit_id=identifier,
                                       repository=repoid)
    users = api_root.get_users()

    squashed_reviewers = set()

    if rrs.total_results > 0:
        squashed_rr = rrs[0]
    else:
        # A review request for that identifier doesn't exist - this
        # is the first push to this identifier and we'll need to create
        # it from scratch.
        squashed_rr = rrs.create(**{
            "extra_data.p2rb": "True",
            "extra_data.p2rb.is_squashed": "True",
            "extra_data.p2rb.identifier": identifier,
            "extra_data.p2rb.discard_on_publish_rids": '[]',
            "extra_data.p2rb.unpublished_rids": '[]',
            "commit_id": identifier,
            "repository": repoid,
        })

    squashed_rr.get_diffs().upload_diff(
        commits["squashed"]["diff"],
        base_commit_id=commits["squashed"].get('base_commit_id', None))

    def extract_reviewers(commit):
        reviewers = set()
        for reviewer in commit.get('reviewers', []):
            # we've already seen this reviewer so we can just add them as a
            # reviewer for this commit.
            if reviewer in squashed_reviewers:
                reviewers.add(reviewer)
                continue

            try:
                # Check to see if this user exists (and sync things up
                # between reviewboard and bugzilla, if necessary).
                r = api_root.get_users(q=reviewer)
                rsp_users = r.rsp['users']

                if not rsp_users:
                    hgresp.append('display unrecognized reviewer: %s' %
                                  reviewer)
                elif len(rsp_users) == 1:
                    username = r.rsp['users'][0]['username']
                    if reviewer == username:
                        reviewers.add(username)
                        squashed_reviewers.add(username)
                    else:
                        hgresp.append('display unrecognized reviewer: %s' %
                                      reviewer)
                elif len(rsp_users) > 1:
                    # If we get multiple users, we'll look for an exact match.
                    # It would be nice to use this at first, but we seem to
                    # need the call to get_users in order to synchronize our
                    # users with bugzilla.
                    r = users.get_item(reviewer)
                    username = r.rsp['user']['username']
                    reviewers.add(username)
                    squashed_reviewers.add(username)
            except APIError as e:
                if e.http_status == 404 and e.error_code == 100:
                    hgresp.append('display unrecognized reviewer: %s' %
                                  str(reviewer))
                else:
                    hgresp.append('display error identifying reviewer: %s: %s' %
                                  (str(reviewer), str(e)))

        return sorted(reviewers)

    def update_review_request(rr, commit):
        """Synchronize the state of a review request with a commit.

        Updates the commit message, refreshes the diff, etc.
        """
        props = {
            "summary": commit['message'].splitlines()[0],
            "description": commit['message'],
            "extra_data.p2rb.commit_id": commit['id'],
        }
        reviewers = extract_reviewers(commit)
        if reviewers:
            props["target_people"] = ','.join(reviewers)
        draft = rr.get_or_create_draft(**props)

        rr.get_diffs().upload_diff(
            commit['diff'],
            parent_diff=commit.get('parent_diff', None),
            base_commit_id=commit.get('base_commit_id', None))

    def get_review_data(rr):
        """Obtain a dictionary containing review metadata.

        The dict consists of plain types (as opposed to RBTools types).

        Some values may be unicode, not str.
        """
        rd = {
            'public': rr.public,
            'status': rr.status,
        }

        thing = rr
        try:
            thing = rr.get_draft()
        except APIError as e:
            # error_code 100 is RB API code for "does not exist."
            if e.http_status != 404 or e.error_code != 100:
                raise

        rd['reviewers'] = [p.title for p in thing.target_people]

        return rd

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

    # A mapping from review request id to the corresponding review request
    # API object.
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

        rr = api_root.get_review_request(review_request_id=rid)
        review_requests[rid] = rr
        review_data[rid] = get_review_data(rr)

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

            rr = api_root.get_review_request(review_request_id=rid)
            update_review_request(rr, commit)
            processed_nodes.add(node)
            node_to_rid[node] = rid
            review_requests[rid] = rr
            review_data[rid] = get_review_data(rr)

            try:
                discard_on_publish_rids.remove(rid)
            except ValueError:
                pass

            break

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
            assumed_old_rid = unclaimed_rids[0]
            unclaimed_rids.pop(0)
            rr = api_root.get_review_request(review_request_id=assumed_old_rid)
            update_review_request(rr, commit)
            processed_nodes.add(commit['id'])
            node_to_rid[node] = assumed_old_rid
            review_requests[assumed_old_rid] = rr
            review_data[assumed_old_rid] = get_review_data(rr)

            try:
                discard_on_publish_rids.remove(assumed_old_rid)
            except ValueError:
                pass

            continue

        # There are no more unclaimed review request IDs. This means we have
        # more commits than before. Create new review requests as appropriate.
        rr = rrs.create(**{
            'extra_data.p2rb': 'True',
            'extra_data.p2rb.is_squashed': 'False',
            'extra_data.p2rb.identifier': identifier,
            'repository': repoid,
        })
        update_review_request(rr, commit)
        processed_nodes.add(commit['id'])
        assert isinstance(rr.id, int)
        node_to_rid[node] = rr.id
        review_requests[rr.id] = rr
        review_data[rr.id] = get_review_data(rr)
        unpublished_rids.append(rr.id)

    # At this point every incoming commit has been accounted for.
    # If there are any remaining review requests, they must belong to
    # deleted commits. (Or, we made a mistake and updated the wrong review
    # request)
    for rid in unclaimed_rids:
        rr = api_root.get_review_request(review_request_id=rid)

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


    squashed_description = []
    for commit in commits['individual']:
        squashed_description.append('/r/%s - %s' % (
            node_to_rid[commit['id']],
            commit['message'].splitlines()[0]))

    squashed_description.extend(['', 'Pull down '])
    if len(commits['individual']) == 1:
        squashed_description[-1] += 'this commit:'
    else:
        squashed_description[-1] += 'these commits:'

    squashed_description.extend([
        '',
        'hg pull -r %s %s' % (commits['individual'][-1]['id'], repo_url),
    ])

    commit_list = []
    for commit in commits['individual']:
        node = commit['id']
        commit_list.append([node, node_to_rid[node]])

    commit_list_json = json.dumps(commit_list)
    depends = ','.join(str(i) for i in sorted(node_to_rid.values()))

    props = {
        'summary': identifier,
        'description': '%s\n' % '\n'.join(squashed_description),
        'depends_on': depends,
        'extra_data.p2rb.commits': commit_list_json,
    }

    if 'base_commit_id' in commits['squashed']:
        props['extra_data.p2rb.base_commit'] = (
            commits['squashed']['base_commit_id'])

    if squashed_reviewers:
        props['target_people'] = ','.join(sorted(squashed_reviewers))
    squashed_draft = squashed_rr.get_or_create_draft(**props)

    squashed_rr.update(**{
        'extra_data.p2rb.discard_on_publish_rids': json.dumps(
            discard_on_publish_rids),
        'extra_data.p2rb.unpublished_rids': json.dumps(
            unpublished_rids),
    })

    review_requests[squashed_rr.id] = squashed_rr
    review_data[squashed_rr.id] = get_review_data(squashed_rr)

    return squashed_rr.id, node_to_rid, review_data


def associate_ldap_username(url, ldap_username, privileged_username,
                            privileged_password, username=None, password=None,
                            userid=None, cookie=None):
    """Associate a Review Board user with an ldap username.

    Will return True if an ldap_username is successfully associated
    with a Review Board account, False otherwise.

    This function does not prove ownership over the provided
    ldap_username, it assumes that has been done by the caller
    (e.g. They have pushed to an ldap authenticated hg server
    over ssh).

    In order to associate an ldap username with a user two sets of
    credentials needs to be provided: A user account with permission
    to change ldap associations, and a user account to be changed
    (privileged_username/privileged_password and
    username/password/cookie/userid respectively).

    The Review Board credentials of the user account to be changed
    are required since we should never associate an ldap username
    with a Review Board account unless the requester has proven
    ownership of the Review Board account.
    """
    # TODO: Provide feedback on what went wrong when we fail to
    # associate the username.

    # TODO: Figure out a better way to make sure bots don't end up
    # associating their ldap account with a Review Board user they
    # are pushing for. Bug 1176008
    if ldap_username == 'bind-autoland@mozilla.com':
        return False

    if not ((username is not None and password is not None) or
            (userid is not None and cookie is not None)):
        return False

    try:
        # We first verify that the provided credentials are valid and
        # retrieve the username associated with that Review Board
        # account.
        with ReviewBoardClient(url, username, password, userid, cookie) as rbc:
            root = rbc.get_root()
            session = root.get_session()

            if not session.authenticated:
                return False

            user = session.get_user()
            username = user.username

        # Now that we have proven ownership over the user, take the provided
        # ldap_username and associate it with the account.
        with ReviewBoardClient(url, privileged_username, privileged_password,
                               None, None) as rbc:
            root = rbc.get_root()
            ext = root.get_extension(
                extension_name='mozreview.extension.MozReviewExtension')
            ldap = ext.get_ldap_associations().get_item(username)
            ldap.update(ldap_username=ldap_username)

    except APIError:
        return False

    return True


class NoCacheTransport(SyncTransport):
    """API transport with disabled caching."""
    def enable_cache(self):
        pass


@contextmanager
def ReviewBoardClient(url, username, password, userid, cookie):
    """Obtain a RBClient instance via a context manager.

    This exists as a context manager because of gross hacks necessary for
    dealing with cookies. ``RBClient`` is coded such that it assumes it is
    being used under a user account and storing cookies is always acceptable.
    There is no way to disable cookie file writing or to tell it to use a file
    object (such as BytesIO) as the cookies database.

    We work around this deficiency by creating a temporary file and using it as
    the cookies database for the lifetime of the context manager. When the
    context manager exits, the temporary cookies file is deleted.
    """
    fd, path = tempfile.mkstemp()
    os.close(fd)
    try:
        if userid and cookie:
            # TODO: This is bugzilla specific code that really shouldn't be inside
            # of this file. The whole bugzilla cookie resource is a hack anyways
            # though so we'll deal with this for now.
            rbc = RBClient(url, cookie_file=path,
                           transport_cls=NoCacheTransport)
            login_resource = rbc.get_path(
                'extensions/rbbz.extension.BugzillaExtension/'
                'bugzilla-cookie-logins/')
            login_resource.create(login_id=userid, login_cookie=cookie)
        else:
            rbc = RBClient(url, username=username, password=password,
                           cookie_file=path, transport_cls=NoCacheTransport)

        yield rbc
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


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
    extra_data = None

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
