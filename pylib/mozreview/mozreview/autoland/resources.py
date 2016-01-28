from __future__ import unicode_literals

import json
import logging

from django.db import transaction
from django.core.cache import cache
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
                              AUTOLAND_REQUEST_IN_PROGRESS,
                              AUTOLAND_TIMEOUT,
                              NOT_PUSHED_PARENT_REVIEW_REQUEST)
from mozreview.extra_data import (
    COMMITS_KEY,
    fetch_commit_data,
    is_parent,
    is_pushed
)

AUTOLAND_REQUEST_TIMEOUT = 10.0
IMPORT_PULLREQUEST_DESTINATION = 'mozreview'
TRY_AUTOLAND_DESTINATION = 'try'

AUTOLAND_LOCK_TIMEOUT = 60 * 60 * 24


def acquire_lock(lock_id):
    """Use the memcached add operation to acquire a global lock"""
    logging.info("Acquiring lock for {0}".format(lock_id))
    return cache.add(lock_id, "true", AUTOLAND_LOCK_TIMEOUT)


def release_lock(lock_id):
    """Release memcached lock with key lock_id"""
    logging.info("Releasing lock for {0}".format(lock_id))
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
    """Resource to kick off Autoland to inbound"""

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
    def create(self, request, review_request_id,
               commit_descriptions, *args, **kwargs):
        try:
            rr = ReviewRequest.objects.get(pk=review_request_id)
        except ReviewRequest.DoesNotExist:
            return DOES_NOT_EXIST

        commit_data = fetch_commit_data(rr)

        if not is_pushed(rr, commit_data) or not is_parent(rr, commit_data):
            logging.error('Failed triggering Autoland because the review '
                          'request is not pushed, or not the parent review '
                          'request.')
            return NOT_PUSHED_PARENT_REVIEW_REQUEST

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

        logging.info('Submitting a request to Autoland for review request '
                     'ID %s for revision %s '
                     % (review_request_id, last_revision))

        autoland_url = ext.get_settings('autoland_url')
        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.get_settings('autoland_user')
        autoland_password = ext.get_settings('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR

        pingback_url = autoland_request_update_resource.get_uri(request)

        logging.info('Telling Autoland to give status updates to %s'
                     % pingback_url)

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
            logging.error('We hit a RequestException when submitting a '
                          'request to Autoland')
            release_lock(lock_id)
            return AUTOLAND_ERROR
        except requests.exceptions.Timeout:
            logging.error('We timed out when submitting a request to '
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

        autoland_request = AutolandRequest.objects.create(
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
            logging.error('Failed triggering Autoland because the review '
                          'request is not pushed, or not the parent review '
                          'request.')
            return NOT_PUSHED_PARENT_REVIEW_REQUEST

        target_repository = rr.repository.extra_data.get(
            'try_repository_url')

        if not target_repository:
            return AUTOLAND_CONFIGURATION_ERROR.with_message(
                'Autoland has not been configured with a proper try URL.')

        last_revision = json.loads(
            commit_data.extra_data.get(COMMITS_KEY))[-1][0]

        ext = get_extension_manager().get_enabled_extension(
            'mozreview.extension.MozReviewExtension')

        logging.info('Submitting a request to Autoland for review request '
                     'ID %s for revision %s '
                     % (review_request_id, last_revision))

        autoland_url = ext.get_settings('autoland_url')
        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.get_settings('autoland_user')
        autoland_password = ext.get_settings('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR

        pingback_url = autoland_request_update_resource.get_uri(request)

        logging.info('Telling Autoland to give status updates to %s'
                     % pingback_url)

        lock_id = get_autoland_lock_id(rr.id, target_repository, last_revision)
        if not acquire_lock(lock_id):
            return AUTOLAND_REQUEST_IN_PROGRESS

        try:
            # We use a hard-coded destination here. If we ever open this up
            # to make the destination a parameter to this resource, we need to
            # verify that the destination is in fact an "scm_level_1"
            # repository to ensure that people don't try to land to inbound
            # using this resource.
            response = requests.post(autoland_url + '/autoland',
                data=json.dumps({
                'ldap_username': request.mozreview_profile.ldap_username,
                'tree': rr.repository.name,
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
            release_lock(lock_id)
            return AUTOLAND_ERROR
        except requests.exceptions.Timeout:
            logging.error('We timed out when submitting a request to '
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

        autoland_request = AutolandRequest.objects.create(
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

        if fields['landed']:
            autoland_request.repository_revision=fields['result']
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

        lock_id = get_autoland_lock_id(rr.id,
                                       autoland_request.repository_url,
                                       autoland_request.push_revision)
        release_lock(lock_id)

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
                            NOT_LOGGED_IN)
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

        testing = ext.get_settings('autoland_testing', False)

        autoland_url = ext.get_settings('autoland_url')
        if not autoland_url:
            return AUTOLAND_CONFIGURATION_ERROR

        autoland_user = ext.get_settings('autoland_user')
        autoland_password = ext.get_settings('autoland_password')

        if not autoland_user or not autoland_password:
            return AUTOLAND_CONFIGURATION_ERROR


        # if we've seen an import for this pullrequest before, see if we have
        # an existing bugid we can reuse. Otherwise, Autoland will attempt to
        # extract one from the pullrequest title and if that fails, file a new
        # bug.
        bugid = None
        prs = ImportPullRequestRequest.objects.filter(
            github_user=github_user,
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
            response = requests.post(
                autoland_url + '/pullrequest/mozreview',
                data=json.dumps({
                    'user': github_user,
                    'repo': github_repo,
                    'pullrequest': pullrequest,
                    'destination': destination,
                    'bzuserid': request.session['Bugzilla_login'],
                    'bzcookie': request.session['Bugzilla_logincookie'],
                    'bugid': bugid,
                    'pingback_url': pingback_url
                }),
                headers={'content-type': 'application/json'},
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

        testing = ext.get_settings('autoland_testing', False)

        if not testing and not request.user.has_perm(
                'mozreview.add_autolandeventlogentry'):
            return PERMISSION_DENIED

        try:
            fields = json.loads(request.body)
            landed = fields['landed']
            for name in fields:
                assert type(fields[name]) == self.fields[name]['type']
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
