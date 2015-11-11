from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from djblets.webapi.decorators import webapi_request_fields
from djblets.webapi.errors import DOES_NOT_EXIST

from reviewboard.webapi.base import WebAPIResource

from .models import FileDiffReviewer


class FileDiffReviewerResource(WebAPIResource):
    model = FileDiffReviewer
    name = 'file_diff_reviewer'
    allowed_methods = ('PUT', 'GET')
    uri_object_key = 'file_diff_reviewer_id'

    def has_access_permissions(*args, **kwargs):
        return True

    @webapi_request_fields(required={
        'reviewed': {
            'type': bool,
            'description': 'Whether this FileDiff was reviewed by this'
                           ' reviewer or not',
        }
    })
    def update(self, request, reviewed, *args, **kwargs):
        """Updates a FileDiffReviewer."""
        try:
            file_diff_reviewer = self.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if request.user.id != file_diff_reviewer.reviewer_id:
            return self.get_no_access_error(request)

        file_diff_reviewer.reviewed = reviewed
        file_diff_reviewer.save()
        serialized_object = {
            'id': file_diff_reviewer.id,
            'file_diff_id': file_diff_reviewer.file_diff_id,
            'reviewer_id': file_diff_reviewer.reviewer_id,
            'reviewed': file_diff_reviewer.reviewed,
            'last_modified': file_diff_reviewer.last_modified
        }

        return 200, {
            self.item_result_key: serialized_object
        }


file_diff_reviewer_resource = FileDiffReviewerResource()
