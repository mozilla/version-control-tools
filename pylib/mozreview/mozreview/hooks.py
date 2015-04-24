from __future__ import unicode_literals

from reviewboard.extensions.hooks import ReviewRequestApprovalHook


class MozReviewApprovalHook(ReviewRequestApprovalHook):
    def is_approved(self, review_request, prev_approved, prev_failure):
        """Change the default message for pending reviews"""

        if prev_approved:
            return True

        if prev_failure == 'The review request has not been marked "Ship It!"':
            return prev_approved, 'Pending Review'

        return prev_approved, prev_failure
