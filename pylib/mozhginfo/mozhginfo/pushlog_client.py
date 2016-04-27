"""
This helps us query information about Mozilla's Mercurial repositories.

Documentation found in here:
https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/pushlog.html

Important notes from the pushlog documentation::

    When implementing agents that consume pushlog data, please keep in mind
    the following best practices:

    * Query by push ID, not by changeset or date.
    * Always specify a startID and endID.
    * Try to avoid full if possible.
    * Always use the latest format version.
    * Don't be afraid to ask for a new pushlog feature to make your life easier.
"""
import logging

import requests

from push import Push
from redo import retry


LOG = logging.getLogger('pushlog_client')
JSON_PUSHES = "%(repo_url)s/json-pushes"
VALID_CACHE = {}
VERSION = 2


class PushlogError(Exception):
    pass


def _pushes_to_list(pushes):
    """accept a list of push objects and return a list of revisions"""
    revisions = []
    for push in pushes:
        revisions = revisions + [changeset.node for changeset in push.changesets]
    return revisions


def query_pushes_by_revision_range(repo_url, from_revision, to_revision, version=VERSION,
                                   tipsonly=True, return_revision_list=False):
    """
    Return an ordered list of pushes (by date - oldest (starting) first).

    repo_url                - represents the URL to clone a repo
    from_revision           - from which revision to start with (oldest)
    to_revision             - from which revision to end with (newest)
    version                 - version of json-pushes to use (see docs)
    tipsonly                - only return the tip most push been returned if it's True
    return_revision_list    - return a list of revisions if it's True
    """
    push_list = []
    url = "%s?fromchange=%s&tochange=%s&version=%d" % (
        JSON_PUSHES % {"repo_url": repo_url},
        from_revision,
        to_revision,
        version
    )

    if tipsonly:
        url += '&tipsonly=1'

    LOG.debug("About to fetch %s" % url)
    req = retry(requests.get, args=(url,))
    pushes = req.json()["pushes"]
    # json-pushes does not include the starting revision
    push_list.append(query_push_by_revision(repo_url, from_revision))

    for push_id in sorted(pushes.keys()):
        # Querying by push ID is perferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the full char representation
        push_list.append(Push(push_id=push_id, push_info=pushes[push_id]))
    if return_revision_list:
        return _pushes_to_list(push_list)

    return push_list


def query_pushes_by_pushid_range(repo_url, start_id, end_id, version=VERSION,
                                 return_revision_list=False):
    """
    Return an ordered list of pushes (oldest first).

    repo_url               - represents the URL to clone a repo
    start_id               - from which pushid to start with (oldest)
    end_id                 - from which pushid to end with (most recent)
    version                - version of json-pushes to use (see docs)
    return_revision_list   - return a list of revisions if it's True
    """
    push_list = []
    url = "%s?startID=%s&endID=%s&version=%s&tipsonly=1" % (
        JSON_PUSHES % {"repo_url": repo_url},
        start_id - 1,  # off by one to compensate for pushlog as it skips start_id
        end_id,
        version
    )
    LOG.debug("About to fetch %s" % url)
    req = retry(requests.get, args=(url,))
    pushes = req.json()["pushes"]

    for push_id in sorted(pushes.keys()):
        # Querying by push ID is preferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the 12 char representation
        push_list.append(Push(push_id=push_id, push_info=pushes[push_id]))
    if return_revision_list:
        return _pushes_to_list(push_list)

    return push_list


def query_pushes_by_specified_revision_range(repo_url, revision, before, after,
                                             return_revision_list=False):
    """
    Get the start and end revisions' pushlog based on the number of revisions before and after.
    Raises PushlogError if pushlog data cannot be retrieved.
    repo_url               - represents the URL to clone a rep
    revision               - the revision used to set the query range
    before                 - the number before the revision given
    after                  - the number after the revision given
    return_revision_list   - return a list of revisions if it's True
    """
    try:
        push = query_push_by_revision(repo_url, revision)
        pushid = int(push.id)
        start_id = pushid - before
        end_id = pushid + after
        push_list = query_pushes_by_pushid_range(repo_url, start_id, end_id)
    except Exception as e:
        LOG.exception(e)
        raise PushlogError('Unable to retrieve pushlog data. '
                           'Please check repo_url and revision specified.')

    if return_revision_list:
        return _pushes_to_list(push_list)

    return push_list


def query_push_by_revision(repo_url, revision, full=False, return_revision_list=False):
    """
    Return a dictionary with meta-data about a push including:

        * changesets
        * date
        * user
    repo_url               - represents the URL to clone a rep
    revision               - the revision used to set the query range
    full                   - query whole information of a push if it's True
    return_revision_list   - return a list of revisions if it's True
    """
    url = "%s?changeset=%s&tipsonly=1" % (JSON_PUSHES % {"repo_url": repo_url}, revision)
    if full:
        url += "&full=1"
    LOG.debug("About to fetch %s" % url)
    req = retry(requests.get, args=(url,))
    data = req.json()
    assert len(data) == 1, "We should only have information about one push"

    if not full:
        LOG.debug("Push info: %s" % str(data))
        push_id, push_info = data.popitem()
        push = Push(push_id=push_id, push_info=push_info)
    else:
        LOG.debug("Requesting the info with full=1 can yield too much unnecessary output "
                  "to debug anything properly")
    if return_revision_list:
        return push.changesets[0].node

    return push


def query_repo_tip(repo_url):
    """Return the tip of a branch URL."""
    url = "%s?tipsonly=1" % (JSON_PUSHES % {"repo_url": repo_url})
    recent_commits = retry(requests.get, args=(url,)).json()
    tip_id = sorted(recent_commits.keys())[-1]
    return Push(push_id=tip_id, push_info=recent_commits[tip_id])


def valid_revision(repo_url, revision):
    """Verify that a revision exists in the given repository URL."""

    global VALID_CACHE
    if (repo_url, revision) in VALID_CACHE:
        return VALID_CACHE[(repo_url, revision)]

    LOG.debug("Determine if the revision is valid.")
    url = "%s?changeset=%s&tipsonly=1" % (
        JSON_PUSHES % {"repo_url": repo_url},
        revision
    )
    data = retry(requests.get, args=(url,)).json()
    ret = True

    # A valid revision will return a dictionary with information about exactly one revision
    if len(data) != 1:
        LOG.warning("Revision %s not found on branch %s" % (revision, repo_url))
        ret = False

    VALID_CACHE[(repo_url, revision)] = ret
    return ret
