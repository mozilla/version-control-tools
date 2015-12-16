"""
This helps us query information about Mozilla's Mercurial repositories.

Documentation found in here:
https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/pushlog.html

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


LOG = logging.getLogger('pushlog_client')
JSON_PUSHES = "%(repo_url)s/json-pushes"
VALID_CACHE = {}


class PushlogError(Exception):
    pass


def query_pushes_by_revision_range(repo_url, from_revision, to_revision, version=2, tipsonly=1):
    """
    Return an ordered list of pushes (by date - oldest (starting) first).

    repo_url      - represents the URL to clone a repo
    from_revision - from which revision to start with (oldest)
    to_revision   - from which revision to end with (newest)
    version       - version of json-pushes to use (see docs)
    """
    push_list = []
    url = "%s?fromchange=%s&tochange=%s&version=%d&tipsonly=%d" % (
        JSON_PUSHES % {"repo_url": repo_url},
        from_revision,
        to_revision,
        version,
        tipsonly
    )
    LOG.debug("About to fetch %s" % url)
    req = requests.get(url)
    pushes = req.json()["pushes"]
    # json-pushes does not include the starting revision
    push_list.append(query_push_by_revision(repo_url, from_revision))

    for push_id in sorted(pushes.keys()):
        # Querying by push ID is perferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the full char representation
        push_list.append(Push(push_id=push_id, push_info=pushes[push_id]))

    return push_list


def query_pushes_by_pushid_range(repo_url, start_id, end_id, version=2):
    """
    Return an ordered list of pushes (oldest first).

    repo_url - represents the URL to clone a repo
    start_id - from which pushid to start with (oldest)
    end_id   - from which pushid to end with (most recent)
    version  - version of json-pushes to use (see docs)
    """
    push_list = []
    url = "%s?startID=%s&endID=%s&version=%s&tipsonly=1" % (
        JSON_PUSHES % {"repo_url": repo_url},
        start_id - 1,  # off by one to compensate for pushlog as it skips start_id
        end_id,
        version
    )
    LOG.debug("About to fetch %s" % url)
    req = requests.get(url)
    pushes = req.json()["pushes"]

    for push_id in sorted(pushes.keys()):
        # Querying by push ID is preferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the 12 char representation
        push_list.append(Push(push_id=push_id, push_info=pushes[push_id]))

    return push_list


def query_push_by_revision(repo_url, revision, full=False):
    """
    Return a dictionary with meta-data about a push including:

        * changesets
        * date
        * user
    """
    url = "%s?changeset=%s&tipsonly=1" % (JSON_PUSHES % {"repo_url": repo_url}, revision)
    if full:
        url += "&full=1"
    LOG.debug("About to fetch %s" % url)
    req = requests.get(url)
    data = req.json()
    assert len(data) == 1, "We should only have information about one push"

    if not full:
        LOG.debug("Push info: %s" % str(data))
        push_id, push_info = data.popitem()
        push = Push(push_id=push_id, push_info=push_info)
    else:
        LOG.debug("Requesting the info with full=1 can yield too much unnecessary output "
                  "to debug anything properly")
    return push


def query_repo_tip(repo_url):
    """Return the tip of a branch URL."""
    url = "%s?tipsonly=1" % (JSON_PUSHES % {"repo_url": repo_url})
    recent_commits = requests.get(url).json()
    tip_id = sorted(recent_commits.keys())[-1]
    return Push(push_id=tip_id, push_info=recent_commits[tip_id])


def valid_revision(repo_url, revision):
    """Verify that a revision exists in the given repository URL."""

    global VALID_CACHE
    if (repo_url, revision) in VALID_CACHE:
        return VALID_CACHE[(repo_url, revision)]

    LOG.debug("Determine if the revision is valid.")
    url = "%s?changeset=%s" % (repo_url, revision)
    data = requests.get(url).json()
    ret = True

    # A valid revision will return a dictionary with information about exactly one revision
    if len(data) != 1:
        LOG.warning("Revision %s not found on branch %s" % (revision, repo_url))
        ret = False

    VALID_CACHE[(repo_url, revision)] = ret
    return ret
