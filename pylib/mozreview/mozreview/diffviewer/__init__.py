from reviewboard.diffviewer.models import DiffSet


def diffstats(diffset):
    """Return a dictionary of diffstat information for a diffset."""
    counts = diffset.get_total_line_counts()

    # TODO: Take into account the non raw counts review board might
    # have to display information about replacement.
    return {
        'insert': counts.get('raw_insert_count', 0),
        'delete': counts.get('raw_delete_count', 0),
    }


def get_diffstats(review_request, user, rev=None):
    """Return a dictionary containing diffstat information.

    If no rev is provided, use the latest diffset. If the requesting
    user is the submitter, take any draft diffsets into account.
    """
    # Ensure we're working with the base review request, not a draft.
    review_request = review_request.get_review_request()

    if rev is None:
        # If the user is the submitter we might want to use the draft diffset.
        draft = review_request.get_draft(user=user)
        diffset = ((draft and draft.diffset) or
                   review_request.get_latest_diffset())
    else:
        diffset = (
            DiffSet.objects
            .filter(history__pk=review_request.diffset_history_id)
            .filter(revision=rev)).latest()

    return diffstats(diffset)
