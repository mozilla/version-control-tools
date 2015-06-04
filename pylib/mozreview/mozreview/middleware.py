from mozreview.models import get_profile, MozReviewUserProfile


class MozReviewUserProfileMiddleware(object):
    """Fetch the MozReviewUserProfile and attach it to the request object."""

    def process_request(self, request):
        if not request.user.is_authenticated():
            request.mozreview_profile = None
            return

        request.mozreview_profile = get_profile(request.user)
