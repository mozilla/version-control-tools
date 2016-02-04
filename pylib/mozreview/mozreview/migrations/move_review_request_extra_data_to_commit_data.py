"""This is a 1-off migration to be run as part of the fix for
https://bugzilla.mozilla.org/show_bug.cgi?id=1244448.
We need to migrate the ReviewRequest and ReviewRequestDraft extra_data
to the CommitData extra_data to prevent the user from changing them using the
review-request(-draft) endpoints.
"""
import json

from reviewboard.reviews.models import ReviewRequest

from mozreview.models import CommitData


for review_request in ReviewRequest.objects.all():
    draft_extra_data = {}
    draft_review_request = review_request.get_draft()

    if draft_review_request:
        draft_extra_data = draft_review_request.extra_data

    CommitData.objects.get_or_create(
        review_request=review_request,
        defaults={
            'extra_data': json.dumps(review_request.extra_data),
            'draft_extra_data': json.dumps(draft_extra_data)
        }
    )
