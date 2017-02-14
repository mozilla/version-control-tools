from __future__ import unicode_literals

import json
import logging

import requests
from django.db import transaction
from django.core.cache import cache
from django.utils import six
from djblets.webapi.decorators import (
    webapi_login_required,
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.webapi.errors import (
    DOES_NOT_EXIST,
    INVALID_FORM_DATA,
    NOT_LOGGED_IN,
    PERMISSION_DENIED,
)
from reviewboard.changedescs.models import ChangeDescription
from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.models import ReviewRequest
from reviewboard.scmtools.models import Repository
from reviewboard.site.urlresolvers import local_site_reverse
from reviewboard.webapi.resources import WebAPIResource

from mozreview.autoland.models import (
    AutolandEventLogEntry,
    AutolandRequest,
)
from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import BugzillaError
from mozreview.decorators import webapi_scm_groups_required
from mozreview.errors import (
    AUTOLAND_CONFIGURATION_ERROR,
    AUTOLAND_ERROR,
    AUTOLAND_REQUEST_IN_PROGRESS,
    AUTOLAND_TIMEOUT,
    NOT_PUSHED_PARENT_REVIEW_REQUEST,
)
from mozreview.extra_data import (
    COMMITS_KEY,
    fetch_commit_data,
    is_parent,
    is_pushed,
)
from mozreview.models import (
    get_bugzilla_api_key,
)

AUTOLAND_REQUEST_TIMEOUT = 10.0
IMPORT_PULLREQUEST_DESTINATION = 'mozreview'
TRY_AUTOLAND_DESTINATION = 'try'

AUTOLAND_LOCK_TIMEOUT = 60 * 60 * 24


logger = logging.getLogger(__name__)


def acquire_lock(lock_id):
    """Use the memcached add operation to acquire a global lock"""
    logger.info("Acquiring lock for {0}".format(lock_id))
    return cache.add(lock_id, "true", AUTOLAND_LOCK_TIMEOUT)


def release_lock(lock_id):
    """Release memcached lock with key lock_id"""
    logger.info("Releasing lock for {0}".format(lock_id))
    cache.delete(lock_id)


def get_autoland_lock_id(review_request_id, repository_url, revision):
    """Returns a lock id based on the given parameters"""
    return 'autoland_lock:{0}:{1}:{2}'.format(
        review_request_id, repository_url, revision)


class BaseAutolandTriggerResource(WebAPIResource):
    """Base resource for Autoland trigger resources.

    Subclasses should inherit from this and provide their own create
    methods with the necessary request fields and scm_level validation.
    """

    allowed_methods = ('POST',)
    model = AutolandRequest

    def has_list_access_permissions(self, request, *args, **kwargs):
        return True

    def serialize_last_known_status_field(self, obj, **kwargs):
        return obj.last_known_status

    def save_autolandrequest_id(self, fieldname, rr, autoland_request_id):
        # TODO: this method is only required while we are using change
        #       descriptions to render autoland results. Once Bug 1176330 is
        #       fixed this code can be removed.

        # There's possibly a race condition here with multiple web-heads. If
        # two requests come in at the same time to this endpoint, the request
        # that saves their value first here will get overwritten by the second
        # but the first request will have their changedescription come below
        # the second. In that case you'd have the "most recent" try build stats
        # appearing at the top be for a changedescription that has a different
        # try build below it (Super rare, not a big deal really).
        old_request_id = rr.extra_data.get(fieldname, None)
        rr.extra_data[fieldname] = autoland_request_id
        rr.save()

        # In order to display the fact that a build was kicked off in the UI,
        # we construct a change description that our TryField can render.
        changedesc = ChangeDescription(public=True, text='', rich_text=False)
        changedesc.record_field_change(fieldname,
                                       old_request_id, autoland_request_id)
        changedesc.save()
        rr.changedescs.add(changedesc)


class AutolandTriggerResource(BaseAutolandTriggerResource):
    """Resource to kick off Autoland to inbound for a review request."""

    name = 'autoland_trigger'

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN)
    @webapi_scm_groups_required('scm_level_3')
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The review request for which to trigger a Try '
                               'build',
            },
            'commit_descriptions': {
                'type': six.text_type,
                'description': 'Commit descriptions which overwrite the repo '
                               'commit message. JSON encoded string.  See '
                               '/autoland route for details.',
            }
        },
    )
    @transaction.atomic
    def create(self, request, review_request_id, commit_descriptions, *args,
               **kwargs):
        try:
            rr = ReviewRequest.objects.get(pk=review_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        commit_data = fetch_commit_data(rr)

        if not is_pushed(rr, commit_data) or not is_parent(rr, commit_data):
            logger.error('Failed triggering Autoland because the review '
                         'request is not pushed, or not the parent review '
                         'request.')
            return NOT_PUSHED_PARENT_REVIEW_REQUEST

        enabled = rr.repository.extra_data.get('autolanding_enabled')

        if not enabled:
            return AUTOLAND_CONFIGURATION_ERROR.with_message(
                'Autolanding not enabled.')

        target_repository = rr.repository.extra_data.get(
            'landing_repository_url')
        push_bookmark = rr.repository.extra_data.get('landing_bookmark')

        if not target_repository:
            return AUTOLAND_CONFIGURATION_ERROR.with_message(
                'Autoland has not been configured with a proper landing URL.')

        last_revision = json.loads(
            commit_data.extra_data.get(COMMITS_KEY))[-1][0]
        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        logger.info('Submitting a request to Autoland for review request '
                    'ID %s for revision %s destination %s' %
                    (review_request_id, last_revision, target_repository))

        autoland_url = ext.get_settings('autoland_url')

        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.get_settings('autoland_user')
        autoland_password = ext.get_settings('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR

        pingback_url = autoland_request_update_resource.get_uri(request)
        lock_id = get_autoland_lock_id(rr.id, target_repository, last_revision)

        if not acquire_lock(lock_id):
            return AUTOLAND_REQUEST_IN_PROGRESS

        try:
            response = requests.post(
                autoland_url + '/autoland',
                data=json.dumps({
                    'ldap_username': request.mozreview_profile.ldap_username,
                    'tree': rr.repository.name,
                    'pingback_url': pingback_url,
                    'rev': last_revision,
                    'destination': target_repository,
                    'push_bookmark': push_bookmark,
                    'commit_descriptions': json.loads(commit_descriptions),
                }),
                headers={
                    'content-type': 'application/json',
                },
                timeout=AUTOLAND_REQUEST_TIMEOUT,
                auth=(autoland_user, autoland_password))
        except requests.exceptions.RequestException:
            logger.error('We hit a RequestException when submitting a '
                         'request to Autoland')
            release_lock(lock_id)
            return AUTOLAND_ERROR
        except requests.exceptions.Timeout:
            logger.error('We timed out when submitting a request to '
                         'Autoland')
            release_lock(lock_id)
            return AUTOLAND_TIMEOUT

        if response.status_code != 200:
            release_lock(lock_id)

            try:
                error_message = response.json().get('error')
            except ValueError:
                error_message = response.text

            return AUTOLAND_ERROR, {
                'status_code': response.status_code,
                'message': error_message,
            }

        # We succeeded in scheduling the job.
        try:
            autoland_request_id = int(response.json().get('request_id', 0))
        finally:
            if autoland_request_id is None:
                release_lock(lock_id)
                return AUTOLAND_ERROR, {
                    'status_code': response.status_code,
                    'request_id': None,
                }

        AutolandRequest.objects.create(
            autoland_id=autoland_request_id,
            push_revision=last_revision,
            repository_url=target_repository,
            review_request_id=rr.id,
            user_id=request.user.id,
        )

        AutolandEventLogEntry.objects.create(
            status=AutolandEventLogEntry.REQUESTED,
            autoland_request_id=autoland_request_id)

        self.save_autolandrequest_id('p2rb.autoland', rr,
                                     autoland_request_id)

        return 200, {}


autoland_trigger_resource = AutolandTriggerResource()


class TryAutolandTriggerResource(BaseAutolandTriggerResource):
    """Resource to kick off Try Builds for a particular review request."""

    name = 'try_autoland_trigger'

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN)
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

        if not try_syntax.startswith('try: '):
            return INVALID_FORM_DATA, {
                'fields': {
                    'try_syntax': ['The provided try syntax was invalid']
                }
            }

        commit_data = fetch_commit_data(rr)

        if not is_pushed(rr, commit_data) or not is_parent(rr, commit_data):
            logger.error('Failed triggering Autoland because the review '
                         'request is not pushed, or not the parent review '
                         'request.')
            return NOT_PUSHED_PARENT_REVIEW_REQUEST

        enabled = rr.repository.extra_data.get('autolanding_to_try_enabled')

        if not enabled:
            return AUTOLAND_CONFIGURATION_ERROR.with_message(
                'Autolanding to try not enabled.')

        target_repository = rr.repository.extra_data.get(
            'try_repository_url')

        if not target_repository:
            return AUTOLAND_CONFIGURATION_ERROR.with_message(
                'Autoland has not been configured with a proper try URL.')

        last_revision = json.loads(
            commit_data.extra_data.get(COMMITS_KEY))[-1][0]
        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        logger.info('Submitting a request to Autoland for review request '
                    'ID %s for revision %s destination try'
                    % (review_request_id, last_revision))

        autoland_url = ext.get_settings('autoland_url')

        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.get_settings('autoland_user')
        autoland_password = ext.get_settings('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR

        pingback_url = autoland_request_update_resource.get_uri(request)

        lock_id = get_autoland_lock_id(rr.id, target_repository, last_revision)

        if not acquire_lock(lock_id):
            return AUTOLAND_REQUEST_IN_PROGRESS

        try:
            # We use a hard-coded destination here. If we ever open this up
            # to make the destination a parameter to this resource, we need to
            # verify that the destination is in fact an "scm_level_1"
            # repository to ensure that people don't try to land to inbound
            # using this resource.
            response = requests.post(
                autoland_url + '/autoland',
                data=json.dumps({
                    'ldap_username': request.mozreview_profile.ldap_username,
                    'tree': rr.repository.name,
                    'pingback_url': pingback_url,
                    'rev': last_revision,
                    'destination': TRY_AUTOLAND_DESTINATION,
                    'trysyntax': try_syntax,
                }),
                headers={
                    'content-type': 'application/json',
                },
                timeout=AUTOLAND_REQUEST_TIMEOUT,
                auth=(autoland_user, autoland_password)
            )
        except requests.exceptions.RequestException:
            logger.error('We hit a RequestException when submitting a '
                         'request to Autoland')
            release_lock(lock_id)
            return AUTOLAND_ERROR
        except requests.exceptions.Timeout:
            logger.error('We timed out when submitting a request to '
                         'Autoland')
            release_lock(lock_id)
            return AUTOLAND_TIMEOUT

        if response.status_code != 200:
            release_lock(lock_id)
            return AUTOLAND_ERROR, {
                'status_code': response.status_code,
                'message': response.json().get('error'),
            }

        # We succeeded in scheduling the job.
        try:
            autoland_request_id = int(response.json().get('request_id', 0))
        finally:
            if autoland_request_id is None:
                release_lock(lock_id)
                return AUTOLAND_ERROR, {
                    'status_code': response.status_code,
                    'request_id': None,
                }

        AutolandRequest.objects.create(
            autoland_id=autoland_request_id,
            push_revision=last_revision,
            repository_url=target_repository,
            review_request_id=rr.id,
            user_id=request.user.id,
            extra_data=json.dumps({
                'try_syntax': try_syntax
            })
        )

        AutolandEventLogEntry.objects.create(
            status=AutolandEventLogEntry.REQUESTED,
            autoland_request_id=autoland_request_id)

        self.save_autolandrequest_id('p2rb.autoland_try', rr,
                                     autoland_request_id)

        return 200, {}


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

        testing = ext.get_settings('autoland_testing', False)

        if not testing and not request.user.has_perm(
                'mozreview.add_autolandeventlogentry'):
            return PERMISSION_DENIED

        try:
            fields = json.loads(request.body)

            for field_name in self.fields:
                assert (type(fields[field_name]) ==
                        self.fields[field_name]['type'])
        except (ValueError, IndexError, KeyError, AssertionError) as e:
            return INVALID_FORM_DATA, {
                'error': '%s' % e,
                }

        try:
            autoland_request = AutolandRequest.objects.get(
                pk=fields['request_id'])
        except AutolandRequest.DoesNotExist:
            return DOES_NOT_EXIST

        rr = ReviewRequest.objects.get(pk=autoland_request.review_request_id)
        bz_comment = None

        if fields['landed']:
            autoland_request.repository_revision = fields['result']
            autoland_request.save()

            # If we've landed to the "inbound" repository, we'll close the
            # review request automatically.
            landing_repo = rr.repository.extra_data.get(
                'landing_repository_url')

            if autoland_request.repository_url == landing_repo:
                rr.close(ReviewRequest.SUBMITTED)

            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.SERVED,
                details=fields['result'])
        elif not fields.get('error_msg') and fields.get('result'):
            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.REQUESTED,
                details=fields['result'])
        else:
            AutolandEventLogEntry.objects.create(
                autoland_request_id=fields['request_id'],
                status=AutolandEventLogEntry.PROBLEM,
                error_msg=fields['error_msg']
            )

            # The error message contains context explaining that Autoland
            # failed, so no leading text is necessary.
            bz_comment = fields['error_msg']

        lock_id = get_autoland_lock_id(rr.id,
                                       autoland_request.repository_url,
                                       autoland_request.push_revision)
        release_lock(lock_id)

        if bz_comment:
            bugzilla = Bugzilla(get_bugzilla_api_key(request.user))
            bug_id = int(rr.get_bug_list()[0])

            # Catch and log Bugzilla errors rather than bubbling them up,
            # since we don't want the Autoland server to continously
            # retry the update.
            try:
                bugzilla.post_comment(bug_id, bz_comment)
            except BugzillaError as e:
                logger.error('Failed to post comment to Bugzilla: %s' % e)

        return 200, {}


autoland_request_update_resource = AutolandRequestUpdateResource()


class AutolandEnableResource(WebAPIResource):
    """Provides interface to enable or disable Autoland for a repository."""

    name = 'autoland_enable'
    uri_name = 'autoland_enable'
    uri_object_key = 'repository'
    allowed_methods = ('GET', 'PUT')

    @webapi_response_errors(DOES_NOT_EXIST, PERMISSION_DENIED)
    def get(self, request, *args, **kwargs):
        try:
            repo = Repository.objects.get(id=kwargs[self.uri_object_key])
        except Repository.DoesNotExist:
            return DOES_NOT_EXIST

        try_enabled = repo.extra_data.get('autolanding_to_try_enabled', False)
        enabled = repo.extra_data.get('autolanding_enabled', False)
        return 200, {
            'autolanding_to_try_enabled': try_enabled,
            'autolanding_enabled': enabled,
        }

    @webapi_response_errors(DOES_NOT_EXIST, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'autolanding_to_try_enabled': {
                'type': bool,
                'description': 'Enable autolanding to try',
            },
            'autolanding_enabled': {
                'type': bool,
                'description': 'Enable autolanding',
            },
        },
    )
    def update(self, request, autolanding_to_try_enabled,
               autolanding_enabled, *args, **kwargs):
        if not request.user.has_perm('mozreview.enable_autoland'):
            logger.info('Could not set autoland enable: permission '
                        'denied for user: %s' % (request.user.id))
            return PERMISSION_DENIED

        try:
            repo = Repository.objects.get(id=kwargs[self.uri_object_key])
        except Repository.DoesNotExist:
            logger.info('Could not set autoland enable: repository %s'
                        'unknown.' % (kwargs[self.uri_object_key]))
            return DOES_NOT_EXIST

        logger.info('Setting autoland enable: repository %s: try: %s '
                    'landing: %s at request of user: %s' % (
                        kwargs[self.uri_object_key],
                        autolanding_to_try_enabled,
                        autolanding_enabled,
                        request.user.id))
        repo.extra_data['autolanding_to_try_enabled'] = autolanding_to_try_enabled
        repo.extra_data['autolanding_enabled'] = autolanding_enabled
        repo.save(update_fields=['extra_data'])

        return 200, {
            'autolanding_to_try_enabled': autolanding_to_try_enabled,
            'autolanding_enabled': autolanding_enabled,
        }


autoland_enable_resource = AutolandEnableResource()
