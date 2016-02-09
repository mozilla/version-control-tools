from mozreview.models import get_profile, MozReviewUserProfile


class MozReviewUserProfileMiddleware(object):
    """Fetch the MozReviewUserProfile and attach it to the request object."""

    def process_request(self, request):
        if not request.user.is_authenticated():
            request.mozreview_profile = None
            return

        request.mozreview_profile = get_profile(request.user)


class MozReviewCacheDisableMiddleware(object):
    """Disable ETAGs for Review Request and Diff pages

    Review Board does not take custom fields into account when generating
    the ETAG for review requests. In order to work around this we selectively
    nuke the ETAG from requests to the page.
    """
    # URL names which should not use etag caching.
    URLNAME_BLACKLIST = [
        'review-request-detail',
        'view-diff',
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        if (request.resolver_match and
            request.resolver_match.url_name in self.URLNAME_BLACKLIST and
            'HTTP_IF_NONE_MATCH' in request.META):
            # Clear the etag provided by the client
            del request.META['HTTP_IF_NONE_MATCH']

    def process_response(self, request, response):
        if (request.resolver_match and
            request.resolver_match.url_name in self.URLNAME_BLACKLIST and
            'ETag' in response):
            # Clear the etag Review Board generated
            del response['ETag']

        return response