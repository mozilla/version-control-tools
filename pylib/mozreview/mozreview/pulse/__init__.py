from __future__ import unicode_literals

import json

from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.models import ReviewRequest
from reviewboard.reviews.signals import review_request_published

from mozillapulse import publishers
from mozillapulse.messages import base

from mozreview.decorators import if_ext_enabled
from mozreview.utils import is_parent, is_pushed


def initialize_pulse_handlers(extension):
    SignalHook(extension, review_request_published,
               handle_commits_published)


@if_ext_enabled
def handle_commits_published(extension=None, **kwargs):
    """Handle sending 'mozreview.commits.published'.

    This message is only sent when the parent review request, in a set of
    pushed review requests, is published with new commit information.

    This is a useful message for consumers who care about new or modified
    commits being published for review.
    """
    review_request = kwargs.get('review_request')

    if (review_request is None or
        not is_pushed(review_request) or
        not is_parent(review_request)):
        return

    # Check the change description and only continue if it contains a change
    # to the commit information. Currently change descriptions won't include
    # information about our extra data field, so we'll look for a change to
    # the diff which is mandatory if the commits changed. TODO: Properly use
    # the commit information once we start populating the change description
    # with it.
    #
    # A change description will not exist if this is the first publish of the
    # review request. In that case we know there must be commits since this
    # is a pushed request.
    cd = kwargs.get('changedesc')
    if (cd is not None and ('diff' not in cd.fields_changed or
                            'added' not in cd.fields_changed['diff'])):
        return

    # TODO: Find a better place to retrieve the repository url since we might
    # want it to be different from path here. This will require a new convention
    # for where to store it, mirror_path might work.
    repo_url = review_request.repository.path

    child_rrids = []
    commits = []
    ext_commits = json.loads(
        review_request.extra_data.get('p2rb.commits', '[]'))

    for rev, rrid in ext_commits:
        child_rrids.append(int(rrid))
        commits.append({
            'rev': rev,
            'review_request_id': int(rrid),
            'diffset_revision': None
        })


    # In order to retrieve the diff revision for each commit we need to fetch
    # their correpsonding child review request.
    review_requests = dict(
        (obj.id, obj) for obj in
        ReviewRequest.objects.filter(pk__in=child_rrids))

    for commit_info in commits:
        # TODO: Every call to get_latest_diffset() makes its own query to the
        # database. It is probably possible to retrieve the diffsets we care
        # about using a single query through Django's ORM, but it's not trivial.
        commit_info['diffset_revision'] = review_requests[
            commit_info['review_request_id']
        ].get_latest_diffset().revision

    msg = base.GenericMessage()
    msg.routing_parts.append('mozreview.commits.published')
    msg.data['parent_review_request_id'] = review_request.id
    msg.data['parent_diffset_revision'] = review_request.get_latest_diffset().revision
    msg.data['commits'] = commits
    msg.data['repository_url'] = repo_url

    publish_message(extension, msg)


def publish_message(extension, msg):
    config = get_pulse_config(extension)
    pulse = publishers.MozReviewPublisher(**config)

    try:
        pulse.publish(msg)
    finally:
        pulse.disconnect()


def get_pulse_config(extension):
    return {
        'host': extension.settings['pulse_host'] or None,
        'port': extension.settings['pulse_port'] or None,
        'ssl': extension.settings['pulse_ssl'] or False,
        'user': extension.settings['pulse_user'] or None,
        'password': extension.settings['pulse_password'] or None,
    }
