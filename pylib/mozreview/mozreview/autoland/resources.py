from __future__ import unicode_literals

import json
import logging

from django.db import transaction
from django.utils import six
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   INVALID_FORM_DATA,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
import requests
from reviewboard.changedescs.models import ChangeDescription
from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.models import ReviewRequest
from reviewboard.site.urlresolvers import local_site_reverse
from reviewboard.webapi.resources import WebAPIResource

from mozreview.autoland.models import (AutolandEventLogEntry,
                                       AutolandRequest)
from mozreview.autoland.errors import (AUTOLAND_ERROR,
                                       AUTOLAND_TIMEOUT,
                                       BAD_AUTOLAND_CREDENTIALS,
                                       BAD_AUTOLAND_URL,
                                       BAD_UPDATE_CREDENTIALS)
from mozreview.errors import NOT_PUSHED_PARENT_REVIEW_REQUEST
from mozreview.utils import is_parent, is_pushed

TRY_AUTOLAND_DESTINATION = 'try'
TRY_AUTOLAND_TREE = 'mozilla-central'
TRY_AUTOLAND_TIMEOUT = 10.0


class TryAutolandTriggerResource(WebAPIResource):
    """Resource for reviewers or reviewees to kick off Try Builds
    for a particular review request."""

    name = 'try_autoland_trigger'
    allowed_methods = ('GET', 'POST',)
    model = AutolandRequest

    fields = {
        'autoland_id': {
            'type': int,
            'description': 'The request ID that Autoland gave back.'
        },
        'push_revision': {
            'type': six.text_type,
            'description': 'The revision of what got pushed for Autoland to '
                           'land.',
        },
        'repository_url': {
            'type': six.text_type,
            'description': 'The repository that Autoland was asked to land '
                           'on.',
        },
        'repository_revision': {
            'type': six.text_type,
            'description': 'The revision of what Autoland landed on the '
                           'repository.',
        },
        'review_request_id': {
            'type': int,
            'description': 'The review request associated with this Autoland '
                           'request.',
        },
        'user_id': {
            'type': int,
            'description': 'The user that initiated the Autoland request.',
        },
        'last_known_status': {
            'type': six.text_type,
            'description': 'The last known status for this request.',
        },
    }

    def has_access_permissions(self, request, *args, **kwargs):
        return False

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The review request for which to trigger a Try '
                               'build',
            },
            'try_syntax': {
                'type': six.text_type,
                'description': 'The TryChooser syntax for the builds that '
                               'will be kicked off',
            },
        },
        optional={
            'autoland_request_id_for_testing': {
                'type': int,
                'description': 'For testing only. If the MozReview extension '
                               'is in testing mode, this skips the request to '
                               'Try Autoland and just uses this request id.'
            }
        }
    )
    @transaction.atomic
    def create(self, request, review_request_id, try_syntax,
               autoland_request_id_for_testing=None, *args, **kwargs):
        try:
            rr = ReviewRequest.objects.get(pk=review_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if not is_pushed(rr) or not is_parent(rr):
            logging.error('Failed triggering Autoland because the review '
                          'request is not pushed, or not the parent review '
                          'request.')
            return NOT_PUSHED_PARENT_REVIEW_REQUEST

        if not rr.is_mutable_by(request.user):
            return PERMISSION_DENIED

        commit_list = json.loads(rr.extra_data.get('p2rb.commits'))
        last_revision = commit_list[-1][0]

        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        testing = ext.settings.get('autoland_testing', False)

        if testing:
            logging.info('In testing mode - storing autoland request id %s'
                         % autoland_request_id_for_testing)
            autoland_request_id = autoland_request_id_for_testing
        else:
            logging.info('Submitting a request to Autoland for review request '
                         'ID %s for revision %s '
                         % (review_request_id, last_revision))

            autoland_url = ext.settings.get('autoland_url')
            if not autoland_url:
                return BAD_AUTOLAND_URL

            autoland_user = ext.settings.get('autoland_user')
            autoland_password = ext.settings.get('autoland_password')

            if not autoland_user or not autoland_password:
                return BAD_AUTOLAND_CREDENTIALS

            endpoint = autoland_request_update_resource.get_uri(request)

            logging.info('Telling Autoland to give status updates to %s'
                         % endpoint)

            try:
                response = requests.post(autoland_url, data=json.dumps({
                    'tree': TRY_AUTOLAND_TREE,
                    'endpoint': endpoint,
                    'rev': last_revision,
                    'destination': TRY_AUTOLAND_DESTINATION,
                    'trysyntax': try_syntax,
                }), headers={
                    'content-type': 'application/json',
                },
                    timeout=TRY_AUTOLAND_TIMEOUT,
                    auth=(autoland_user, autoland_password))
            except requests.exceptions.RequestException:
                logging.error('We hit a RequestException when submitting a '
                              'request to Autoland')
                return AUTOLAND_ERROR
            except requests.exceptions.Timeout:
                logging.error('We timed out when submitting a request to '
                              'Autoland')
                return AUTOLAND_TIMEOUT

            if response.status_code != 200:
                return AUTOLAND_ERROR, {
                    'status_code': response.status_code,
                    'message': response.json().get('error'),
                }

            # We succeeded in scheduling the job.
            try:
                autoland_request_id = int(response.json().get('request_id', 0))
            finally:
                if autoland_request_id is None:
                    return AUTOLAND_ERROR, {
                        'status_code': response.status_code,
                        'request_id': autoland_request_id,
                    }

        autoland_request = AutolandRequest.objects.create(
            autoland_id=autoland_request_id,
            push_revision=last_revision,
            review_request_id=rr.id,
            user_id=request.user.id,
            extra_data=json.dumps({
                'try_syntax': try_syntax
            })
        )

        AutolandEventLogEntry.objects.create(
            status=AutolandEventLogEntry.REQUESTED,
            autoland_request=autoland_request)

        # There's possibly a race condition here with multiple web-heads. If
        # two requests come in at the same time to this endpoint, the request
        # that saves their value first here will get overwritten by the second
        # but the first request will have their changedescription come below
        # the second. In that case you'd have the "most recent" try build stats
        # appearing at the top be for a changedescription that has a different
        # try build below it (Super rare, not a big deal really).
        old_request_id = rr.extra_data.get('p2rb.autoland_try', None)
        rr.extra_data['p2rb.autoland_try'] = autoland_request_id
        rr.save()

        # In order to display the fact that a build was kicked off in the UI,
        # we construct a change description that our TryField can render.
        changedesc = ChangeDescription(public=True, text='', rich_text=False)
        changedesc.record_field_change('p2rb.autoland_try',
                                       old_request_id, autoland_request_id)
        changedesc.save()
        rr.changedescs.add(changedesc)

        return 200, {
            self.item_result_key: autoland_request,
        }

    def serialize_last_known_status_field(self, obj, **kwargs):
        return obj.last_known_status


try_autoland_trigger_resource = TryAutolandTriggerResource()


class AutolandRequestUpdateResource(WebAPIResource):
    """Resource for notifications of Autoland requests status update"""
    name = 'autoland_request_update'
    allowed_methods = ('POST',)
    fields = {
        'request_id': {
            'type': int,
            'description': 'ID of the Autoland request this event refers to'
        },
        'destination': {
            'type': six.text_type,
            'description': 'Repository where the push landed'
        },
        'landed': {
            'type': bool,
            'description': 'Whether this push landed or not'
        },
        'result': {
            'type': six.text_type,
            'description': 'Either an error message or the revision of the '
                           'push landed'
        },
        'rev': {
            'type': six.text_type,
            'description': 'The revision of what got pushed for Autoland to'
                           'grab'
        },
        'tree': {
            'type': six.text_type,
            'description': 'Origin of this push'
        },
        'trysyntax': {
            'type': six.text_type,
            'description': 'The TryChooser syntax for the builds we will kick '
                           'off'
        }
    }

    def has_access_permissions(self, request, *args, **kwargs):
        return False

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    def get_uri(self, request):
        # TODO - remove this before landing. Just for local testing on mconley's machine
        #return "http://192.168.59.3:60353/api/extensions/mozreview.extension.MozReviewExtension/autoland-request-updates/"
        named_url = self._build_named_url(self.name_plural)

        return request.build_absolute_uri(
            local_site_reverse(named_url, request=request, kwargs={}))

    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_login_required
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        testing = ext.settings.get('autoland_testing', False)

        if not testing:
            if not request.user.has_perm('mozreview.autoland.autoland_add'):
                return BAD_UPDATE_CREDENTIALS

        try:
            fields = json.loads(request.body)
            for field_name, field_definition in self.fields.items():
                assert type(fields[field_name]) == field_definition['type']
        except (ValueError, IndexError, AssertionError) as e:
            return INVALID_FORM_DATA, {
                'error': e,
            }

        try:
            AutolandRequest.objects.get(pk=fields['request_id'])
        except AutolandRequest.DoesNotExist:
            return INVALID_FORM_DATA

        update_queryset = AutolandRequest.objects.filter(
            pk=fields['request_id'])

        if fields['landed']:
            update_queryset.filter(pk=fields['request_id']).update(
                repository_revision=fields['result']
            )

        status = (AutolandEventLogEntry.SERVED if fields['landed'] else
                  AutolandEventLogEntry.PROBLEM)

        AutolandEventLogEntry.objects.create(
            autoland_request_id=fields['request_id'],
            status=status,
            details=fields['result'],
        )

        return 200, {}


autoland_request_update_resource = AutolandRequestUpdateResource()
