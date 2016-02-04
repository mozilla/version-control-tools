from __future__ import unicode_literals

import logging

from reviewboard.extensions.hooks import ReviewRequestApprovalHook

from mozreview.extra_data import (
    COMMIT_ID_KEY,
    fetch_commit_data,
    gen_child_rrs,
    is_parent,
    is_pushed,
)
from mozreview.models import (
    get_profile,
)
from mozreview.review_helpers import (
    has_valid_shipit,
    has_l3_shipit,
)


class MozReviewApprovalHook(ReviewRequestApprovalHook):
    """Calculates landing approval for review requests.

    This hook allows us to control the `approved` and `approval_failure`
    fields on review request model instances, and Web API results
    associated with them. By calculating landing approval and returning
    it here we have a nice way to distribute this decision throughout
    Review Board.
    """

    def is_approved(self, review_request, prev_approved, prev_failure):
        """Check if a review request is approved to land

        We will completely override the checks done by Review Board and
        provide our own (to keep approval simpler and explicit).

        If True is returned by this function it will indicate that
        review request may be autolanded - care should be taken
        when modifying the logic.
        """
        # TODO: We should consider rejecting review requests which
        # currently have a draft (to prevent autolanding incorrect
        # things)
        try:
            if not is_pushed(review_request):
                return False, 'Manually uploaded requests cannot be approved.'

            if not review_request.public:
                return False, 'The review request is not public.'

            if is_parent(review_request):
                return self.is_approved_parent(review_request)

            return self.is_approved_child(review_request)
        except Exception as e:
            # We catch all exceptions because any error will make
            # Review Board revert to it's default behaviour which
            # is much more relaxed than ours.
            logging.error('Failed to calculate approval for review '
                          'request %s: %s' % (review_request.id, e))
            return False, "Error when calculating approval."

    def is_approved_parent(self, review_request):
        """Check approval for a parent review request"""
        children = list(gen_child_rrs(review_request))

        if not children:
            # This parent review request had no children, so it's either
            # private or something has gone seriously wrong.
            logging.error('Review request %s has no children' %
                          review_request.id)
            return False, 'Review request has no children.'

        for rr in children:
            if not rr.approved:
                commit_data = fetch_commit_data(rr)
                commit_id = commit_data.extra_data.get(COMMIT_ID_KEY, None)

                if commit_id is None:
                    logging.error('Review request %s missing commit_id'
                                  % rr.id)
                    return False, 'A Commit is not approved.'

                return False, 'Commit %s is not approved.' % commit_id

        return True

    def is_approved_child(self, review_request):
        """Check approval for a child review request"""
        if review_request.shipit_count == 0:
            return False, 'A suitable reviewer has not given a "Ship It!"'

        if review_request.issue_open_count > 0:
            return False, 'The review request has open issues.'

        # TODO: Add a check that we have executed a try build of some kind.

        author_mrp = get_profile(review_request.submitter)

        # TODO: Make these "has_..." methods return the set of reviews
        # which match the criteria so we can indicate which reviews
        # actually gave the permission to land.
        if author_mrp.has_scm_ldap_group('scm_level_3'):
            # In the case of a level 3 user we really only care that they've
            # received a single ship-it, which is still current, from any
            # user. If they need to wait for reviews from other people
            # before landing we trust them to wait.
            if not has_valid_shipit(review_request):
                return False, 'A suitable reviewer has not given a "Ship It!"'
        else:
            if not has_l3_shipit(review_request):
                return False, 'A suitable reviewer has not given a "Ship It!"'

        return True
