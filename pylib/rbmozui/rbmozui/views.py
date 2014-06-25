from django.shortcuts import (get_object_or_404, get_list_or_404, redirect,
                              render, render_to_response)
from django.template.context import RequestContext

from reviewboard.reviews.models import ReviewRequest
from reviewboard.reviews.views import _find_review_request

def commits(request, review_request_id, local_site=None, template_name='rbmozui/commits.html'):
    # Use a private method here, because why re-invent the wheel?
    # Still, we might want to fork this ourselves, or have Review Board
    # core expose something better publicly.
    review_request, response = _find_review_request(
        request, review_request_id, local_site)

    if not review_request:
        return response

    if review_request.extra_data.get('p2rb.is_squashed', 'False') == 'True':
      response = render_to_response(template_name, RequestContext(request, {
          'review_request': review_request
      }))
      return response

    # We only want squashed commits here. If what we've got is not
    # a squashed commit, we do one of two things:
    # 1) If the review request is not part of a squashed set, just
    #    redirect to the review request details page for this review request.
    if review_request.extra_data.get('p2rb', 'False') == 'False':
      # TODO: Should do some logging here.
      return redirect(review_request)

    # 2) If the review request is not a squashed commit, but belongs to
    #    a squashed commit, redirect to the squashed commit.
    identifier = review_request.extra_data.get('p2rb.identifier', None)
    if not identifier:
      # TODO: Should do some logging here, or maybe something more intelligent
      raise Http404

    # By convention, the identifer should map to a commit_id on the squashed
    # review request.
    review_requests = ReviewRequest.objects.filter(commit_id=identifier)

    if len(review_requests) < 1:
      # TODO: some logging...
      raise Http404

    if len(review_requests) > 1:
      # TODO: Do some logging, because we broke our invariant...
      pass

    review_request = review_requests[0]
    return redirect('rbmozui.views.commits', review_request_id=review_request.id)
