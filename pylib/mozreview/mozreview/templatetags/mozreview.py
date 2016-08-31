from __future__ import absolute_import

from django import template
from django.contrib.auth.models import User
from django.utils.safestring import SafeString

from mozreview.diffs import (
    latest_revision_reviewed,
)
from mozreview.diffviewer import (
    get_diffstats,
)
from mozreview.extra_data import (
    COMMIT_ID_KEY,
    COMMIT_MSG_FILEDIFF_IDS_KEY,
    fetch_commit_data,
    is_parent,
    is_pushed,
    REVIEW_FLAG_KEY,
)
from mozreview.review_helpers import get_reviewers_status

from reviewboard.reviews.models import (
    ReviewRequestDraft,
)


register = template.Library()


@register.filter()
def isSquashed(review_request):
    return is_parent(review_request)


@register.filter()
def isPush(review_request):
    return is_pushed(review_request)


@register.filter()
def isDraft(review_request):
    return isinstance(review_request, ReviewRequestDraft)


@register.filter()
def commit_id(review_request_details):
    """Return the commit id of a review request or review request draft"""
    commit_data = fetch_commit_data(review_request_details)
    return str(commit_data.get_for(review_request_details, COMMIT_ID_KEY))


@register.filter()
def commit_message_filediff_ids(review_request_details):
    """Return the commit message FileDiff ids of a ReviewRequest or Draft"""
    commit_data = fetch_commit_data(review_request_details)
    return commit_data.get_for(review_request_details,
                               COMMIT_MSG_FILEDIFF_IDS_KEY, default='[]')


def reviewer_list(review_request):
    return ', '.join([user.username
                      for user in review_request.target_people.all()])


@register.filter()
def extra_data(review_request, key):
    return review_request.extra_data[key]

@register.filter()
def review_flag(review):
    flag = review.extra_data[REVIEW_FLAG_KEY]
    if flag == ' ':
        return 'Review flag cleared'

    return 'Review flag: %s' % flag

@register.filter()
def scm_level(mozreview_profile):
    if mozreview_profile is None:
        return ''
    elif mozreview_profile.has_scm_ldap_group('scm_level_3'):
        return '3'
    elif mozreview_profile.has_scm_ldap_group('scm_level_2'):
        return '2'
    elif mozreview_profile.has_scm_ldap_group('scm_level_1'):
        return '1'
    else:
        return ''


@register.filter()
def data_reviewed_revision(review_request, user):
    """Return the latest diff revision a user reviewed.

    `0`, a revision number which will never exist, is returned
    if the user has not performed a review.
    """
    return latest_revision_reviewed(review_request, user=user) or 0


@register.filter()
def required_ldap_group(repository):
    try:
        return repository.extra_data['required_ldap_group']
    except (AttributeError, KeyError):
        return ''


@register.filter()
def autolanding_to_try_enabled(repository):
    try:
        return ('true' if repository.extra_data['autolanding_to_try_enabled']
                else 'false')
    except (AttributeError, KeyError):
        return 'false'


@register.filter()
def autolanding_enabled(repository):
    try:
        return ('true' if repository.extra_data['autolanding_enabled']
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
def trychooser_url(repository):
    try:
        return repository.extra_data['trychooser_url']
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
def reviewer_status_with_drive_by(review_request, reviewer):
    reviewer_status = get_reviewers_status(review_request,
                                           reviewers=[reviewer],
                                           include_drive_by=True)
    return reviewer_status[reviewer.username]


@register.filter()
def userid_to_user(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 'Unknown user'


@register.filter()
def review_flag_class(review_flag):
    reviewer_status_class_map = {
        'r?': 'review-pending',
        'r+': 'review-granted',
        'r-': 'review-denied',
        ' ': 'review-cleared'
    }
    return reviewer_status_class_map.get(review_flag)


@register.filter()
def diffstat_text(review_request, user):
    stat = get_diffstats(review_request, user)
    insert = separator = delete = ''

    if stat['insert'] != 0:
        insert = diffstat_rounded_label(stat['insert'])

    if stat['insert'] != 0 and stat['delete'] != 0:
        separator = ' / '

    if stat['delete'] != 0:
        delete = diffstat_rounded_label(stat['delete'], False)

    return SafeString('%s%s%s' % (insert, separator, delete))


def diffstat_rounded_label(num, is_addition=True):
    base = 1000
    template = '<span class="diffstat-%s">%s%s</span>'
    label = '%s' % (num if num < base else '%.1fk' % (float(num) / base))

    if is_addition:
        return template % ('insert', '+', label)
    else:
        return template % ('delete', '-', label)
