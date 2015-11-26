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


LOG = logging.getLogger('pushlog_client')
JSON_PUSHES = "%(repo_url)s/json-pushes"
VALID_CACHE = {}


class PushlogError(Exception):
    pass


def query_revisions_range(repo_url, from_revision, to_revision, version=2, tipsonly=1):
    """
    Return an ordered list of revisions (by date - oldest (starting) first).

    repo           - represents the URL to clone a repo
    from_revision - from which revision to start with (oldest)
    to_revision   - from which revision to end with (newest)
    version        - version of json-pushes to use (see docs)
    """
    revisions = []
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
    revisions.append(from_revision)
    for push_id in sorted(pushes.keys()):
        # Querying by push ID is perferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the full char representation
        revisions.append(pushes[push_id]["changesets"][-1])

    return revisions


def query_pushid_range(repo_url, start_id, end_id, version=2):
    """
    Return an ordered list of revisions (newest push id first).

    repo     - represents the URL to clone a repo
    start_id - from which pushid to start with (oldest)
    end_id   - from which pushid to end with (most recent)
    version  - version of json-pushes to use (see docs)
    """
    revisions = []
    url = "%s?startID=%s&endID=%s&version=%s&tipsonly=1" % (
        JSON_PUSHES % {"repo_url": repo_url},
        start_id - 1,  # off by one to compensate for pushlog as it skips start_id
        end_id,
        version
    )
    LOG.debug("About to fetch %s" % url)
    req = requests.get(url)
    pushes = req.json()["pushes"]
    # pushes.keys() is a list of strings which we need to map to integers
    # We use reverse in order to return list sorted from newest to oldest push id
    for push_id in sorted(map(int, pushes.keys()), reverse=True):
        # Querying by push ID is preferred because date ordering is
        # not guaranteed (due to system clock skew)
        # We can interact with self-serve with the 12 char representation
        revisions.append(pushes[str(push_id)]["changesets"][0])

    return revisions


def query_revisions_range_from_revision_before_and_after(repo_url, revision, before, after):
    """
    Get the start and end revisions based on the number of revisions before and after.

    Raises PushlogError if pushlog data cannot be retrieved.
    """
    try:
        push_info = query_revision_info(repo_url, revision)
        pushid = int(push_info["pushid"])
        start_id = pushid - before
        end_id = pushid + after
        revlist = query_pushid_range(repo_url, start_id, end_id)
    except:
        raise PushlogError('Unable to retrieve pushlog data. '
                           'Please check repo_url %s and revision %s specified.'
                           % (repo_url, revision))

    return revlist


def query_revision_info(repo_url, revision, full=False):
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
    push_id, push_info = data.popitem()
    push_info["pushid"] = push_id
    if not full:
        LOG.debug("Push info: %s" % str(push_info))
    else:
        LOG.debug("Requesting the info with full=1 can yield too much unnecessary output "
                  "to debug anything properly")
    return push_info


def query_full_revision_info(repo_url, revision):
    """
    Return the full 40 chars revision number which correspond to the revision
    number we given, and throw an error out if found collision in there.

    :param repo_url: The repo url of a repository
                     e.g. http://hg.mozilla.org/integration/mozilla-inbound
    :param revision: push revision (40 chars)
    :type revision: str
    :return:
    """
    push_info = query_revision_info(repo_url, revision)
    if not push_info:
        raise PushlogError("Unable to retrieve pushlog info by repo_url: %s"
                           " and revision: %s. Maybe The revision doesn't exist in the repo"
                           " or We don't have enough characters to determine the revision "
                           "Please check repo_url and revision secified."
                           % (repo_url, revision))
    return push_info['changesets'][0]


def query_repo_tip(repo_url):
    """Return the tip of a branch."""
    url = "%s?tipsonly=1" % (JSON_PUSHES % {"repo_url": repo_url})
    recent_commits = requests.get(url).json()
    tip_id = sorted(map(int, recent_commits.keys()))[-1]
    return recent_commits[str(tip_id)]["changesets"][0]


def valid_revision(repo_url, revision):
    """Verify that a revision exists in the given repository."""

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
