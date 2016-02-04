from __future__ import absolute_import

import logging

from django import template
from django.contrib.auth.models import User

from mozreview.extra_data import (
    COMMIT_ID_KEY,
    fetch_commit_data,
    is_parent,
    MOZREVIEW_KEY,
)
from mozreview.review_helpers import get_reviewers_status

register = template.Library()


@register.filter()
def isSquashed(review_request):
    return is_parent(review_request)

@register.filter()
def isPush(aReviewRequest):
    return str(aReviewRequest.extra_data.get(MOZREVIEW_KEY, 'False')).lower() == 'true'


@register.filter()
def commit_id(review_request_details):
    """Return the commit id of a review request or review request draft"""
    commit_data = fetch_commit_data(review_request_details)
    return str(commit_data.get_for(review_request_details, COMMIT_ID_KEY))


def reviewer_list(review_request):
    return ', '.join([user.username
                      for user in review_request.target_people.all()])

@register.filter()
def extra_data(review_request, key):
    return review_request.extra_data[key]


@register.filter()
def scm_level(mozreview_profile):
    if mozreview_profile is None:
        return ''
    elif mozreview_profile.has_scm_ldap_group('scm_level_3'):
        return '3'
    elif mozreview_profile.has_scm_ldap_group('scm_level_1'):
        return '1'


@register.filter()
def required_ldap_group(repository):
    try:
        return repository.extra_data['required_ldap_group']
    except (AttributeError, KeyError):
        return ''


@register.filter()
def has_try_repository(repository):
    try:
        return ('true' if repository.extra_data['try_repository_url']
                else 'false')
    except (AttributeError, KeyError):
        return 'false'


@register.filter()
def landing_repository(repository):
    try:
        return repository.extra_data['landing_repository_url']
    except (AttributeError, KeyError):
        return ''


@register.filter()
def treeherder_repo(landing_url):
    mapping = {
        'try': 'try',
        'ssh://hg.mozilla.org/try': 'try',
        'ssh://hg.mozilla.org/projects/cedar': 'cedar',
        'ssh://hg.mozilla.org/integration/mozilla-inbound': 'mozilla-inbound',
    }

    return mapping.get(landing_url.rstrip('/'), '')

@register.filter()
def mercurial_repo_name(landing_url):
    return landing_url.rstrip('/').split('/')[-1]


@register.filter()
def ssh_to_https(landing_url):
    return landing_url.rstrip('/').replace('ssh://', 'https://')


@register.filter()
def reviewers_status(review_request):
    return get_reviewers_status(review_request).items()

@register.filter()
def userid_to_user(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 'Unknown user'
