def is_pushed(review_request):
    """Is this a review request that was pushed to MozReview."""
    return str(review_request.extra_data.get('p2rb', False)).lower() == 'true'

def is_parent(review_request):
    """Is this a MozReview 'parent' review request.

    If this review request represents the folded diff parent of each child
    review request we will return True. This will return false on each of the
    child review requests (or a request which was not pushed).
    """
    return str(review_request.extra_data.get(
        'p2rb.is_squashed', False)).lower() == 'true'
