from __future__ import unicode_literals

import json
import logging

from django.template.loader import Context, get_template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.fields import BaseReviewRequestField
from reviewboard.reviews.models import ReviewRequest, ReviewRequestDraft

from mozreview.utils import is_parent, is_pushed

from mozreview.autoland.models import AutolandRequest, AutolandEventLogEntry


def get_root(review_request):
    if not is_parent(review_request):
        identifier = review_request.extra_data.get('p2rb.identifier')
        try:
            review_request = ReviewRequest.objects.get(
                commit_id=identifier, repository=review_request.repository)
        except:
            logging.error('Could not retrieve root review request with '
                          'commit id %s because it does not appear to exist, '
                          'or the user does not have read access to it.'
                          % identifier)
            return None

    return review_request


def ensure_review_request(review_request_details):
    if isinstance(review_request_details, ReviewRequestDraft):
        review_request_details = review_request_details.get_review_request()

    return review_request_details


class CombinedReviewersField(BaseReviewRequestField):
    """ This field allows for empty pushes on the parent request"""
    field_id = "p2rb.reviewer_epoch"

    can_record_change_entry = True

    def should_render(self, value):
        return False

    def get_change_entry_sections_html(self, info):
        return []


class CommitsListField(BaseReviewRequestField):
    """The commits list field for review requests.

    This field is injected in the details of a review request that
    is a "push" based review request.
    """
    field_id = "p2rb.commits"
    label = _("Commits")

    can_record_change_entry = True

    def has_value_changed(self, old_value, new_value):
        # Just to be safe, we de-serialize the json and compare values
        if old_value is not None and new_value is not None:
            return json.loads(old_value) != json.loads(new_value)
        return old_value != new_value

    def should_render(self, value):
        return is_pushed(self.review_request_details)

    def get_change_entry_sections_html(self, info):
        return []

    def as_html(self):
        rr = ensure_review_request(self.review_request_details)

        root_rr = get_root(rr)

        template = get_template('mozreview/commits.html')
        return template.render(Context({
            'current_id': rr.id,
            'root_rr': root_rr,
        }))


class TryField(BaseReviewRequestField):
    """The field for kicking off Try builds and showing Try state.

    This field allows a user to kick off a Try build for each unique
    revision. Once kicked off, it shows the state of the most recent
    Try build.
    """
    field_id = 'p2rb.autoland_try'
    label = _('Try')

    can_record_change_entry = True

    _retreive_error_txt = _('There was an error retrieving the try push.')
    _waiting_txt = _('Waiting for autoland request to execute, hold tight.')
    _autoland_problem = _('Autoland reported a problem: %s')
    _job_url = 'https://treeherder.mozilla.org/embed/resultset-status/try/%s/'

    def should_render(self, value):
        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        if not ext or not ext.settings.get('autoland_try_ui_enabled'):
            return False

        return is_parent(self.review_request_details)

    def load_value(self, review_request_details):
        return review_request_details.extra_data.get('p2rb.autoland_try')

    def get_change_entry_sections_html(self, info):
        if 'new' not in info:
            # If there was no new value we won't bother rendering anything.
            # this would really only happen if the latest try build was
            # removed and not replaced with a new one, which would be very
            # strange.
            return []

        return [{
            'title': self.label,
            'rendered_html': mark_safe(self.render_change_entry_html(info)),
        }]

    def render_change_entry_html(self, info):
        try:
            autoland_id = int(info['new'][0])
        except (ValueError, TypeError):
            # Something unexpected was recorded as the autoland id in the
            # changedescription. This either means we have a serious bug or
            # someone was attempting to change the field themselves (possibly
            # maliciously).
            logging.error('A malformed autoland_id was detected: %s' %
                          info['new'][0])
            return self._retreive_error_txt

        try:
            ar = AutolandRequest.objects.get(pk=autoland_id)
        except:
            logging.error('An unknown autoland_id was detected: %s' %
                info['new'][0])
            return self._retreive_error_txt

        if ar.last_known_status == AutolandEventLogEntry.REQUESTED:
            return self._waiting_txt
        elif ar.last_known_status == AutolandEventLogEntry.PROBLEM:
            return self._autoland_problem % ar.last_error_msg
        elif ar.last_known_status == AutolandEventLogEntry.SERVED:
            url = self._job_url % ar.repository_revision
            template = get_template('mozreview/try_result.html')
            return template.render(Context({'url': url}))
        else:
            return self._retreive_error_txt

    def as_html(self):
        rr = ensure_review_request(self.review_request_details)

        template = get_template('mozreview/try.html')
        current_autoland_try = rr.extra_data.get('p2rb.autoland_try', None)

        if current_autoland_try is not None:
            current_autoland_try = int(current_autoland_try)

        return template.render(Context({
            'autoland_try': current_autoland_try,
        }))
