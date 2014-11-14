import json
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

    @property
    def can_record_change_entry(self):
        return True

    def should_render(self, value):
        is_p2rb = str(self.review_request_details.extra_data.get('p2rb', False))
        return is_p2rb == "True"

    def load_value(self, review_request_details):
        return review_request_details.extra_data.get('p2rb.reviewer_epoch')

    def render_change_entry_html(self, info):
        return ""

    def as_html(self):
        rr = self.review_request_details
        current_id = self.review_request_details.id

        is_squashed = str(rr.extra_data.get('p2rb.is_squashed', False)) == "True"

        if not is_squashed:
            identifier = rr.extra_data.get('p2rb.identifier')
            try:
                rr = ReviewRequest.objects.get(commit_id=identifier)
                # If the review request isn't public, then the person viewing this
                # must have access permissions on it, and can view the draft.
                if not rr.public:
                    rr = rr.get_draft()
            except:
                logging.error('Could not retrieve child review request with '
                              'commit id %s because it does not appear to exist.'
                              % identifier)
                return ""

        # We can assume that if we're rendering, that we're a pushed review
        # request, so these keys should exist.
        child_rrs = get_child_review_requests(rr)

        template = get_template('rbmozui/commits.html')
        return template.render(Context({
                'child_rrs': child_rrs,
                'current_id': current_id,
                'root_rr': rr,
                'is_draft': isinstance(rr, ReviewRequestDraft)
               }))


def get_child_review_requests(rr):
    is_draft = isinstance(rr, ReviewRequestDraft)

    child_rrs = []
    commit_tuples = json.loads(rr.extra_data.get('p2rb.commits', '{}'))
    for commit_tuple in commit_tuples:
        rid = commit_tuple[1]
        try:
            child = ReviewRequest.objects.get(pk=rid)
            if is_draft and child.get_draft() is not None:
                child = child.get_draft()
            child_rrs.append([commit_tuple[0], child])
        except:
            logging.error('Could not retrieve child review request with '
                          'rid %s because it does not appear to exist.'
                          % rid)
    return child_rrs