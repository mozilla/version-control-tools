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
from reviewboard.scmtools.models import Repository
from reviewboard.site.urlresolvers import local_site_reverse
from reviewboard.webapi.resources import WebAPIResource

from mozreview.autoland.models import (AutolandEventLogEntry,
                                       AutolandRequest,
                                       ImportPullRequestRequest)
from mozreview.decorators import webapi_scm_groups_required
from mozreview.errors import (AUTOLAND_CONFIGURATION_ERROR,
                              AUTOLAND_ERROR,
                              AUTOLAND_TIMEOUT,
                              NOT_PUSHED_PARENT_REVIEW_REQUEST)
from mozreview.extra_data import is_parent, is_pushed

AUTOLAND_REQUEST_TIMEOUT = 10.0
IMPORT_PULLREQUEST_DESTINATION = 'mozreview'
TRY_AUTOLAND_DESTINATION = 'try'


class TryAutolandTriggerResource(WebAPIResource):
    """Resource to kick off Try Builds for a particular review request.

    Only reviewers can start a Try Build.
    """

    name = 'try_autoland_trigger'
    allowed_methods = ('POST',)
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

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_scm_groups_required('scm_level_1')
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
    )
    @transaction.atomic
    def create(self, request, review_request_id, try_syntax, *args, **kwargs):
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

        last_revision = json.loads(rr.extra_data.get('p2rb.commits'))[-1][0]

        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        testing = ext.settings.get('autoland_testing', False)

        logging.info('Submitting a request to Autoland for review request '
                     'ID %s for revision %s '
                     % (review_request_id, last_revision))

        autoland_url = ext.settings.get('autoland_url')
        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.settings.get('autoland_user')
        autoland_password = ext.settings.get('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR

        pingback_url = autoland_request_update_resource.get_uri(request)

        logging.info('Telling Autoland to give status updates to %s'
                     % pingback_url)

        try_autoland_tree = rr.repository.name

        try:
            response = requests.post(autoland_url + '/autoland',
                data=json.dumps({
                'tree': try_autoland_tree,
                'pingback_url': pingback_url,
                'rev': last_revision,
                'destination': TRY_AUTOLAND_DESTINATION,
                'trysyntax': try_syntax,
            }), headers={
                'content-type': 'application/json',
            },
                timeout=AUTOLAND_REQUEST_TIMEOUT,
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
                    'request_id': None,
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
            autoland_request_id=autoland_request_id)

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
    """Resource for notifications of Autoland requests status update."""

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
            'description': 'In case of success, this is the revision of the '
                           'push landed'
        },
        'error_msg': {
            'type': six.text_type,
            'description': 'An error message in case something went wrong'
        },
        'rev': {
            'type': six.text_type,
            'description': 'The revision requested to land'
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

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    def get_uri(self, request):
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

        if not testing and not request.user.has_perm(
                'mozreview.add_autolandeventlogentry'):
            return PERMISSION_DENIED

        try:
            fields = json.loads(request.body)
            landed = fields['landed']
            # result and error_msg are mutually exclusive
            filtered_field = 'error_msg' if landed else 'result'
            mandatory_fields = [f for f in self.fields if f != filtered_field]
            for field_name in mandatory_fields:
                assert type(fields[field_name]) == self.fields[field_name]['type']
        except (ValueError, IndexError, AssertionError) as e:
            return INVALID_FORM_DATA, {
                'error': e,
                }
        try:
            AutolandRequest.objects.get(pk=fields['request_id'])
        except AutolandRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if landed:
            AutolandRequest.objects.filter(pk=fields['request_id'])\
            .update(repository_revision=fields['result'])

            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.SERVED,
                details=fields['result'])
        else:
            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.PROBLEM,
                error_msg=fields['error_msg']
            )

        return 200, {}


autoland_request_update_resource = AutolandRequestUpdateResource()


class ImportPullRequestTriggerResource(WebAPIResource):
    """Resource to import pullrequests."""

    name = 'import_pullrequest_trigger'
    allowed_methods = ('POST',)
    model = ImportPullRequestRequest

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
            'github_user': {
                'type': six.text_type,
                'description': 'The github user for the pullrequest',
            },
            'github_repo': {
                'type': six.text_type,
                'description': 'The github repo for the pullrequest',
            },
            'pullrequest': {
                'type': int,
                'description': 'The pullrequest number',
            },
        },
    )
    @transaction.atomic
    def create(self, request, github_user, github_repo, pullrequest, *args,
               **kwargs):

        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        testing = ext.settings.get('autoland_testing', False)

        autoland_url = ext.settings.get('autoland_url')
        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.settings.get('autoland_user')
        autoland_password = ext.settings.get('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR


        # if we've seen an import for this pullrequest before, see if we have
        # an existing bugid we can reuse. Otherwise, Autoland will attempt to
        # extract one from the pullrequest title and if that fails, file a new
        # bug.
        bugid = None
        prs = ImportPullRequestRequest.objects.filter(github_user=github_user,
                                                      github_repo=github_repo,
                                                      github_pullrequest=pullrequest)
        prs = prs.order_by('-pk')[0:1]
        if prs:
            bugid = prs[0].bugid

        pingback_url = import_pullrequest_update_resource.get_uri(request)

        logging.info('Submitting a request to Autoland for pull request'
                     '%s/%s/%s for bug %s with pingback_url %s'
                     % (github_user, github_repo, pullrequest, bugid,
                        pingback_url))

        destination = IMPORT_PULLREQUEST_DESTINATION
        if testing:
            # This is just slightly better than hard coding the repo name
            destination = Repository.objects.all()[0].name

        try:
            response = requests.post(autoland_url + '/pullrequest/mozreview',
                data=json.dumps({
                'user': github_user,
                'repo': github_repo,
                'pullrequest': pullrequest,
                'destination': destination,
                'bzuserid': request.session['Bugzilla_login'],
                'bzcookie': request.session['Bugzilla_logincookie'],
                'bugid': bugid,
                'pingback_url': pingback_url
            }), headers={
                'content-type': 'application/json',
            },
                timeout=AUTOLAND_REQUEST_TIMEOUT,
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
            request_id = int(response.json()['request_id'])
        except KeyError, ValueError:
            return AUTOLAND_ERROR, {
                'status_code': response.status_code,
                'request_id': autoland_request_id,
            }

        import_pullrequest_request = ImportPullRequestRequest.objects.create(
            autoland_id=request_id,
            github_user=github_user,
            github_repo=github_repo,
            github_pullrequest=pullrequest,
        )

        AutolandEventLogEntry.objects.create(
            status=AutolandEventLogEntry.REQUESTED,
            autoland_request_id=request_id)

        url = autoland_url + '/pullrequest/mozreview/status/' + str(request_id)
        return 200, {'status-url': url}

    def get_uri(self, request):
        named_url = self._build_named_url(self.name_plural)

        return request.build_absolute_uri(
            local_site_reverse(named_url, request=request, kwargs={}))

    def serialize_last_known_status_field(self, obj, **kwargs):
        return obj.last_known_status


import_pullrequest_trigger_resource = ImportPullRequestTriggerResource()


class ImportPullRequestUpdateResource(WebAPIResource):
    """Resource for notifications of pullrequest import status update."""

    name = 'import_pullrequest_update'
    allowed_methods = ('POST',)
    fields = {
        'request_id': {
            'type': int,
            'description': 'ID of the Autoland request this event refers to',
        },
        'bugid': {
            'type': int,
            'description': 'The bugid for the pullrequest',
        },
        'landed': {
            'type': bool,
            'description': 'Whether the import succeeded or not',
        },
        'result': {
            'type': six.text_type,
            'description': 'In case of success, this is the review request '
                           'associated with the pullrequest',
        },
        'error_msg': {
            'type': six.text_type,
            'description': 'An error message in case something went wrong',
        },
    }

    def has_access_permissions(self, request, *args, **kwargs):
        return False

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    def get_uri(self, request):
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

        if not testing and not request.user.has_perm(
                'mozreview.add_autolandeventlogentry'):
            return PERMISSION_DENIED

        try:
            fields = json.loads(request.body)
            landed = fields['landed']
            for field_name in fields:
                assert type(fields[field_name]) == self.fields[field_name]['type']
        except (ValueError, IndexError, AssertionError) as e:
            return INVALID_FORM_DATA, {
                'error': e,
                }

        try:
            ImportPullRequestRequest.objects.get(pk=fields['request_id'])
        except ImportPullRequestRequest.DoesNotExist:
            return DOES_NOT_EXIST

        if landed:
            # Autoland gives us a review request url, we need to extract the id
            try:
                review_request_id = int(fields['result'].split('/')[-1])
            except ValueError as e:
                return INVALID_FORM_DATA, {'error': e}

            ImportPullRequestRequest.objects.filter(
                pk=fields['request_id']).update(
                review_request_id=review_request_id, bugid=fields['bugid'])

            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.SERVED,
                details=fields['result'])
        else:
            # We need to store the bugid even if the import failed so we can
            # use that same bug for later imports of this pullrequest.
            ImportPullRequestRequest.objects.filter(
                pk=fields['request_id']).update(bugid=fields['bugid'])

            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.PROBLEM,
                error_msg=fields['error_msg']
            )

        return 200, {}


import_pullrequest_update_resource = ImportPullRequestUpdateResource()
