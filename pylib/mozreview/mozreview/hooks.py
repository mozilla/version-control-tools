from __future__ import unicode_literals

import logging

from django.template.loader import Context
from django.utils.translation import ugettext as _

from reviewboard.extensions.hooks import (
    ReviewRequestApprovalHook,
    ReviewRequestFieldsHook,
    TemplateHook
)

from mozreview.autoland.models import AutolandEventLogEntry, AutolandRequest
from mozreview.extra_data import (
    COMMIT_ID_KEY,
    fetch_commit_data,
    gen_child_rrs,
    get_parent_rr,
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


logger = logging.getLogger(__name__)

class CommitContextTemplateHook(TemplateHook):
    """Gathers all information required for commits table

    This hook allows us to generate a detailed, custom commits table.
    Information provided includes the parent and child review requests,
    as well as autoland information.
    """

    def get_extra_context(self, request, context):
        """Fetches relevant review request information, returns context"""
        review_request_details = context['review_request_details']
        commit_data = fetch_commit_data(review_request_details)

        user = request.user
        parent = get_parent_rr(review_request_details.get_review_request(), commit_data=commit_data)
        parent_details = parent.get_draft(user) or parent

        # If a user can view the parent draft they should also have
        # permission to view every child. We check if the child is
        # accessible anyways in case it has been restricted for other
        # reasons.
        children_details = [
            child for child in gen_child_rrs(parent_details, user=user)
            if child.is_accessible_by(user)]
        n_children = len(children_details)
        current_child_num = prev_child = next_child = None

        if not is_parent(review_request_details, commit_data=commit_data):
            cur_index = children_details.index(review_request_details)
            current_child_num = cur_index + 1
            next_child = (children_details[cur_index + 1]
                          if cur_index + 1 < n_children else None)
            prev_child = (children_details[cur_index - 1]
                          if cur_index - 1 >= 0 else None)

        latest_autoland_requests = []
        repo_urls = set()
        autoland_requests = AutolandRequest.objects.filter(
            review_request_id=parent.id).order_by('-autoland_id')

        # We would like to fetch the latest AutolandRequest for each
        # different repository.
        for request in autoland_requests:
            if request.repository_url in repo_urls:
                continue

            repo_urls.add(request.repository_url)
            latest_autoland_requests.append(request)

        return {
            'review_request_details': review_request_details,
            'parent_details': parent_details,
            'children_details': children_details,
            'num_children': n_children,
            'current_child_num': current_child_num,
            'next_child': next_child,
            'prev_child': prev_child,
            'latest_autoland_requests': latest_autoland_requests,
            'user': user,
        }

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
            logger.error('Failed to calculate approval for review '
                         'request %s: %s' % (review_request.id, e))
            return False, "Error when calculating approval."

    def is_approved_parent(self, review_request):
        """Check approval for a parent review request"""
        children = list(gen_child_rrs(review_request))

        if not children:
            # This parent review request had no children, so it's either
            # private or something has gone seriously wrong.
            logger.error('Review request %s has no children' %
                         review_request.id)
            return False, 'Review request has no children.'

        for rr in children:
            if not rr.approved:
                commit_data = fetch_commit_data(rr)
                commit_id = commit_data.extra_data.get(COMMIT_ID_KEY, None)

                if commit_id is None:
                    logger.error('Review request %s missing commit_id'
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
