"""Push commits to Review Board.

This module contains code for taking commits from version control (Git,
Mercurial, etc) and adding them to Review Board.

It is intended for this module to be generic and applicable to any
Review Board install. Please abstract away Mozilla implementation
details.
"""

import json

from rbtools.api.client import RBClient
from rbtools.api.errors import APIError


def post_reviews(url, repoid, identifier, commits, username=None, password=None,
                 userid=None, cookie=None):
    """Post a set of commits to Review Board.

    Repository hooks can use this function to post a set of pushed commits
    to Review Board. Each commit will become its own review request.
    Additionally, a review request with a diff encompassing all the commits
    will be created; This "squashed" review request will represent the push
    for the provided `identifier`.

    The `identifier` is a unique string which represents a series of pushed
    commit sets. This identifier is used to update review requests with a new
    set of diffs from a new push. Generally this identifier will represent
    some unit of work, such as a bug.

    The `commits` argument takes the following form:

        {
            'squashed': {
                'diff': <squashed-diff-string>,
            },
            'individual': [
                {
                    'id': <commit-id>,
                    'rid': <previus-review-request-id>,
                    'message': <commit-message>,
                    'diff': <diff>,
                    'parent_diff': <diff-from-base-to-commit>,
                },
                {
                    ...
                },
                ...
            ]
        }
    """
    rbc = RBClient(url, username=username, password=password)
    api_root = rbc.get_root()

    # Retrieve the squashed review request or create it.
    previous_commits = []
    squashed_rr = None
    rrs = api_root.get_review_requests(commit_id=identifier,
                                       repository=repoid)

    if rrs.total_results > 0:
        squashed_rr = rrs[0]
    else:
        # A review request for that identifier doesn't exist - this
        # is the first push to this identifier and we'll need to create
        # it from scratch.
        data = {
            "extra_data.p2rb": "True",
            "extra_data.p2rb.is_squashed": "True",
            "extra_data.p2rb.identifier": identifier,
            "commit_id": identifier,
            "repository": repoid,
        }
        squashed_rr = rrs.create(data=data)

    squashed_rr.get_diffs().upload_diff(commits["squashed"]["diff"])

    def update_review(rid, commit):
        rr = api_root.get_review_request(review_request_id=rid)
        draft = rr.get_or_create_draft(
            commit_id=commit['id'],
            summary=commit['message'].splitlines()[0],
            description=commit['message'])
        rr.get_diffs().upload_diff(commit['diff'],
                                   parent_diff=commit['parent_diff'])

        return rr

    previous_commits = get_previous_commits(squashed_rr)
    remaining_nodes = dict((t[0], t[1]) for i, t in enumerate(previous_commits))
    unclaimed_rids = [t[1] for t in previous_commits]
    processed_nodes = set()
    node_to_rid = {}
    reviews = {}

    # Do a pass and find all commits that map cleanly to old reviews.
    for commit in commits['individual']:
        node = commit['id']

        # If the commit appears in an old review, by definition of commits
        # deriving from content, the commit has not changed and there
        # is nothing to update.
        # TODO handle the review ID of the commit changing. Can this happen?
        if node in remaining_nodes:
            rid = remaining_nodes[node]
            del remaining_nodes[node]
            unclaimed_rids.remove(rid)
            processed_nodes.add(node)
            node_to_rid[node] = rid

            rr = api_root.get_review_request(review_request_id=rid)
            reviews[rid] = rr
            continue

        # We haven't seen this commit before.

        # The client may tell us what review it is associated with. If so,
        # listen to the client, for they are always right.
        if commit['rid']:
            for n, rid in remaining_nodes.items():
                if rid == commit['rid']:
                    del remaining_nodes[n]
                    unclaimed_rids.remove(rid)
                    break

            rr = update_review(commit['rid'], commit)
            processed_nodes.add(node)
            node_to_rid[node] = commit['rid']
            reviews[commit['rid']] = rr
            continue

    # Now do a pass over the commits that didn't map cleanly.
    for commit in commits['individual']:
        node = commit['id']
        if node in processed_nodes:
            continue

        # We haven't seen this commit before *and* the client doesn't know
        # where it belongs.

        # This is where things could get complicated. We could involve
        # heuristic based matching (comparing commit messages, changed
        # files, etc). We may do that in the future.

        # For now, match the commit up against the next one in the index.
        if unclaimed_rids:
            assumed_old_rid = unclaimed_rids[0]
            unclaimed_rids.pop(0)
            rr = update_review(assumed_old_rid, commit)
            processed_nodes.add(commit['id'])
            node_to_rid[node] = assumed_old_rid
            reviews[assumed_old_rid] = rr
            continue

        # There are no more unclaimed review IDs. This means we have more
        # commits than before. Create new reviews as appropriate.
        rr = rrs.create(data={
            'extra_data.p2rb': 'True',
            'extra_data.p2rb.is_squashed': 'False',
            'extra_data.p2rb.identifier': identifier,
            'commit_id': commit['id'],
            'repository': repoid,
        })
        rr.get_diffs().upload_diff(commit['diff'],
                                   parent_diff=commit['parent_diff'])
        draft = rr.get_or_create_draft(
            summary=commit['message'].splitlines()[0],
            description=commit['message'])
        processed_nodes.add(commit['id'])
        # Normalize all review identifiers to strings.
        assert isinstance(rr.id, int)
        rid = str(rr.id)
        node_to_rid[node] = rid
        reviews[rid] = rr

    # At this point every incoming commit has been accounted for.
    # If there are any remaining reviews, they must belong to deleted
    # commits. (Or, we made a mistake and updated the wrong review.)
    for rid in unclaimed_rids:
        rr = api_root.get_review_request(review_request_id=rid)
        rr.update(status='discarded')

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

    squashed_description.extend(
        ['', 'hg pull review -r %s' % commits['individual'][-1]['id']])

    depends = ','.join(str(i) for i in sorted(node_to_rid.values()))
    squashed_draft = squashed_rr.get_or_create_draft(
        summary='Review for review ID: %s' % identifier,
        description='%s\n' % '\n'.join(squashed_description),
        depends_on=depends)

    commit_list = []
    for commit in commits['individual']:
        node = commit['id']
        commit_list.append([node, node_to_rid[node]])

    squashed_rr.update(data={
        'extra_data.p2rb.commits': json.dumps(commit_list)})
    reviews[str(squashed_rr.id)] = squashed_rr

    return str(squashed_rr.id), node_to_rid, reviews

def get_previous_commits(squashed_rr):
    """Retrieve the previous commits from a squashed review request.

    This will return a list of tuples specifying the previous commit
    id as well as the review request it is represented by. ex::
        [
            # (<commit-id>, <review-request-id>),
            ('d4bd89322f54', '13'),
            ('373537353134', '14'),
        ]
    """
    extra_data = squashed_rr.extra_data
    if 'p2rb.commits' not in extra_data:
        return []

    commits = []
    for node, rid in json.loads(extra_data['p2rb.commits']):
        # JSON decoding likes to give us unicode types. We speak str
        # internally, so convert.
        if isinstance(node, unicode):
            node = node.encode('utf-8')

        if isinstance(rid, unicode):
            rid = rid.encode('utf-8')
        elif isinstance(rid, int):
            rid = str(rid)

        assert isinstance(node, str)
        assert isinstance(rid, str)

        commits.append((node, rid))

    return commits
