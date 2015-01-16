import logging

from django.template.loader import Context, get_template
from django.utils.translation import ugettext_lazy as _

from reviewboard.reviews.fields import BaseReviewRequestField
from reviewboard.reviews.models import ReviewRequest, ReviewRequestDraft


class CommitsListField(BaseReviewRequestField):
    """The commits list field for review requests.

    This field is injected in the details of a review request that
    is a "push" based review request.
    """
    field_id = "p2rb.reviewer_epoch"
    label = _("Commits")

    can_record_change_entry = True

    def should_render(self, value):
        is_p2rb = str(self.review_request_details.extra_data.get('p2rb', False))
        return is_p2rb == "True"

    def load_value(self, review_request_details):
        return review_request_details.extra_data.get('p2rb.reviewer_epoch')

    def render_change_entry_html(self, info):
        return ""

    def as_html(self):
        rr = self.review_request_details
        if isinstance(self.review_request_details, ReviewRequestDraft):
            rr = self.review_request_details.get_review_request()

        current_id = rr.id
        is_squashed = str(rr.extra_data.get('p2rb.is_squashed', False)) == "True"

        if not is_squashed:
            identifier = rr.extra_data.get('p2rb.identifier')
            try:
                rr = ReviewRequest.objects.get(commit_id=identifier)
            except:
                logging.error('Could not retrieve child review request with '
                              'commit id %s because it does not appear to exist, or '
                              'the user does not have read access to it.'
                              % identifier)
                return ""

        template = get_template('rbmozui/commits.html')
        return template.render(Context({
            'current_id': current_id,
            'root_rr': rr,
        }))
