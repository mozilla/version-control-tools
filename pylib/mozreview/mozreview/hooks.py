from __future__ import unicode_literals

import logging

from reviewboard.extensions.hooks import ReviewRequestApprovalHook

from mozreview.extra_data import (COMMIT_ID_KEY,
                                  gen_child_rrs,
                                  is_parent,
                                  is_pushed)
from mozreview.models import get_profile


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
        for rr in gen_child_rrs(review_request):
            if not rr.approved:
                commit_id = rr.extra_data.get(COMMIT_ID_KEY, None)

                if commit_id is None:
                    logging.error('Review request %s missing commit_id' % rr.id)
                    return False, 'A Commit is not approved.'

                return False, 'Commit %s is not approved.' % commit_id
        else:
            # This parent review request had no children, so it's either
            # private or something has gone seriously wrong.
            logging.error('Review request %s has no children' %
                          review_request.id)
            return False, 'Review request has no children.'

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


def gen_latest_reviews(review_request):
    """Generate a series of relevant reviews.

    Generate the set of reviews for a review request where there is
    only a single review for each user and it is that users most
    recent review.
    """
    last_user = None
    relevant_reviews = review_request.get_public_reviews().order_by(
        'user', '-timestamp')

    for review in relevant_reviews:
        if review.user == last_user:
            # We only care about the most recent review for each
            # particular user.
            continue

        last_user = review.user
        yield review


def has_valid_shipit(review_request):
    """Return whether the review request has received a valid ship-it.

    A boolean will be returned indicating if the review request has received
    a ship-it from any user on the reviewing users most recent review (i.e.
    a reviewer has provided a ship-it and has not since given a review
    without a ship-it).
    """
    for review in gen_latest_reviews(review_request):
        # TODO: Should we require that the ship-it comes from a review
        # which the review request submitter didn't create themselves?
        if review.ship_it:
            return True

    return False


def has_l3_shipit(review_request):
    """Return whether the review request has received a current L3 ship it.

    A boolean will be returned indicating if the review request has received
    a ship-it from an L3 user that is still valid. In order to be valid the
    ship-it must have been provided after the latest diff has been uploaded.
    """
    diffset_history = review_request.diffset_history

    if not diffset_history:
        # There aren't any published diffs so we should just consider
        # any ship-its meaningless.
        return False

    if not diffset_history.last_diff_updated:
        # Although I'm not certain when this field will be empty
        # it has "blank=true, null=True" - we'll assume there is
        # no published diff.
        return False

    for review in gen_latest_reviews(review_request):
        if not review.ship_it:
            continue

        # TODO: We might want to add a required delay between when the
        # diff is posted and when a review is published - this would
        # avoid a malicious user from timing a diff publish immediately
        # before a reviewer publishes a ship-it on the previous diff
        # (Making it look like the ship-it came after the new diff)
        if review.timestamp <= diffset_history.last_diff_updated:
            continue

        if get_profile(review.user).has_scm_ldap_group('scm_level_3'):
            return True

    return False
