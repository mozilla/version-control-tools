from __future__ import unicode_literals

import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   INVALID_FORM_DATA,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
from reviewboard.diffviewer.models import FileDiff
from reviewboard.reviews.models import BaseComment, Review
from reviewboard.webapi.resources import resources, WebAPIResource


class BatchReviewResource(WebAPIResource):
    """Resource for creating a review with a single request.

    This resource allows automation to create a full review using a single
    POST request. Using the traditional API would result in a high volume
    of requests which would take longer and create stress on the server.

    Each user may only have one review draft per request at a time. Using
    this resource skips the draft stage allowing concurrent review of a
    single request by creating the review and publishing it in a single
    transaction.
    """
    name = 'batch_review'
    allowed_methods = ('GET', 'POST',)

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The ID of the review request.',
            },
        },
        optional={
            'ship_it': {
                'type': bool,
                'description': 'Whether or not to mark the review "Ship It!"',
            },
            'body_top': {
                'type': str,
                'description': 'The review content above the comments.',
            },
            'body_bottom': {
                'type': str,
                'description': 'The review content below the comments.',
            },
            'diff_comments': {
                'type': str,
                'description': 'A JSON payload containing the diff comments.',
            },
        },
    )
    def create(self, request, review_request_id, ship_it=False, body_top='',
               body_bottom='', diff_comments=None, *args, **kwargs):
        """Creates a new review and publishes it.

        Each diff comment provided requires the following information:
        <filediff-id>: int - The primary key of the filediff in the database.
        <first-line>: int - The row number the comment range begins on.
        <num-lines>: int - The number of lines to comment on, starting at.
                           <first-line>.
        <text>: string - The body of the comment to create.
        <issue-opened>: boolean - Whether to open an issue with this comment.

        This information is specified in the diff_comments JSON object which
        takes the following form:
            [
                {
                    'filediff_id': <filediff-id>,
                    'first_line': <first-line>,
                    'num_lines': <num-lines>,
                    'text': <text>,
                    'issue_opened': <issue-opened>,
                }
                ...
            ]
        """
        try:
            review_request = resources.review_request.get_object(
                request,
                review_request_id=review_request_id,
                *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if not review_request.is_accessible_by(request.user):
            return PERMISSION_DENIED

        if body_top is None:
            body_top = ''

        if body_bottom is None:
            body_bottom = ''

        if diff_comments is not None:
            try:
                diff_comments = json.loads(diff_comments)
            except ValueError:
                return INVALID_FORM_DATA, {
                    'fields': {
                        'diff_comments': 'Not valid JSON.',
                    },
                }

            if not isinstance(diff_comments, list):
                return INVALID_FORM_DATA, {
                    'fields': {
                        'diff_comments': 'Does not decode to a list.',
                    },
                }
        else:
            diff_comments = []

        # Wrap all of the database access for this review in a transaction
        # so that if any of the diff_comments are malformed (such as providing
        # non-existent file-diff ids) we will roll everything back.
        try:
            with transaction.atomic():
                review = Review.objects.create(
                    review_request=review_request,
                    user=request.user,
                    body_top=body_top,
                    body_bottom=body_bottom,
                    ship_it=ship_it)

                for comment in diff_comments:
                    filediff = FileDiff.objects.get(
                        pk=comment['filediff_id'],
                        diffset__history__review_request=review_request)

                    if comment.get('issue_opened', False):
                        issue = True
                        issue_status = BaseComment.OPEN
                    else:
                        issue = False
                        issue_status = None

                    review.comments.create(
                        filediff=filediff,
                        interfilediff=None,
                        text=comment.get('text', ''),
                        first_line=comment['first_line'],
                        num_lines=comment['num_lines'],
                        issue_opened=issue,
                        issue_status=issue_status)

                review.publish(user=request.user)

        except KeyError:
            return INVALID_FORM_DATA, {
                'fields': {
                    'diff_comments': 'Diff comments were malformed',
                },
            }

        except ObjectDoesNotExist:
            return INVALID_FORM_DATA, {
                'fields': {
                    'diff_comments': 'Invalid filediff_id',
                },
            }

        return 201, {
            self.item_result_key: review,
        }


batch_review_resource = BatchReviewResource()
