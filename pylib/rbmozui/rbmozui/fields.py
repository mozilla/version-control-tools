from __future__ import unicode_literals

import logging

from django.template.loader import Context, get_template
from django.utils.translation import ugettext as _

from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.fields import BaseReviewRequestField
from reviewboard.reviews.models import ReviewRequest, ReviewRequestDraft

from mozreview.utils import is_parent, is_pushed


def get_root(review_request):
    if not is_parent(review_request):
        identifier = review_request.extra_data.get('p2rb.identifier')
        try:
            review_request = ReviewRequest.objects.get(commit_id=identifier)
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


class CommitsListField(BaseReviewRequestField):
    """The commits list field for review requests.

    This field is injected in the details of a review request that
    is a "push" based review request.
    """
    field_id = "p2rb.reviewer_epoch"
    label = _("Commits")

    can_record_change_entry = True

    def should_render(self, value):
        return is_pushed(self.review_request_details)

    def load_value(self, review_request_details):
        return review_request_details.extra_data.get('p2rb.reviewer_epoch')

    def render_change_entry_html(self, info):
        return ""

    def as_html(self):
        rr = ensure_review_request(self.review_request_details)

        root_rr = get_root(rr)

        template = get_template('rbmozui/commits.html')
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

    def should_render(self, value):
        ext = get_extension_manager().get_enabled_extension(
            'rbmozui.extension.RBMozUI')

        if not ext or not ext.settings.get('autoland_try_ui_enabled'):
            return False

        return is_parent(self.review_request_details)

    def load_value(self, review_request_details):
        return review_request_details.extra_data.get('p2rb.autoland_try')

    def render_change_entry_html(self, info):
        # TODO
        return ""

    def as_html(self):
        rr = ensure_review_request(self.review_request_details)

        template = get_template('rbmozui/try.html')
        current_autoland_try = int(rr.extra_data.get('p2rb.autoland_try'))
        return template.render(Context({
            'autoland_try': current_autoland_try or None,
        }))
