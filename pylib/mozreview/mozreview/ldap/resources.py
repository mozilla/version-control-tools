from __future__ import unicode_literals

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import six
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
from reviewboard.webapi.resources import resources, WebAPIResource
from reviewboard.webapi.resources.user import UserResource

from mozreview.ldap import (
    associate_employee_ldap,
    get_ldap_connection,
    LDAPAssociationException,
)
from mozreview.models import (
    get_profile,
    MozReviewUserProfile,
)


logger = logging.getLogger(__name__)


class LDAPAssociationResource(WebAPIResource):
    """Resource for updating or retrieving the ldap username for a user."""

    name = 'ldap_association'
    uri_object_key = 'username'
    uri_object_key_regex = r'[A-Za-z0-9@\._\-\'\+]+'
    allowed_methods = ('GET', 'PUT')
    fields = {
        'user': {
            'type': UserResource,
            'description': 'The Review Board user',
        },
        'ldap_username': {
            'type': six.text_type,
            'description': 'LDAP username authorized for use',
        },
    }

    def has_access_permissions(self, request, *args, **kwargs):
        return (
            request.user.is_authenticated() and (
                request.user.has_perm('mozreview.modify_ldap_association') or
                request.user.username == kwargs.get(self.uri_object_key)))

    def has_list_access_permissions(self, request, *args, **kwargs):
        # The list returns no information so we don't care who views it.
        return True

    def get_href(self, obj, request, *args, **kwargs):
        """Return the uri to this item.

        In order to have Review Board's get_links machinary work properly
        we must pass a truthy `obj` into it. `obj` will only be used inside
        of get_href to find the url to this item, but since we're not using
        an actual model we just do what RB does when you don't have an `obj`,
        return the current url.
        """
        return request.build_absolute_uri()

    def create_item_payload(self, request, user, profile, *args, **kwargs):
        """Create an item payload for a given user and profile."""
        return {
            'links': self.get_links(self.item_child_resources, request=request,
                                    obj=True, *args, **kwargs),
            self.item_result_key: {
                # TODO: Once MozReview is using a djblets release containing
                # commit c33bd0d4a3a1, we should replace this dictionary
                # creation with: `self.serialize_link(user, *args, **kwargs)`.
                'user': {
                    'method': 'GET',
                    'href': self.get_serializer_for_object(user).get_href(
                        user, request, *args, **kwargs),
                    'title': user.username,
                },
                'ldap_username': profile.ldap_username,
            },
        }

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    def get(self, request, *args, **kwargs):
        """Return the ldap association for a particular user."""
        if not self.has_access_permissions(request, *args, **kwargs):
            return PERMISSION_DENIED

        try:
            # Since this resources uri_object_key matches that of the
            # UserResource we should properly query for the requested
            # username.
            user = resources.user.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            # This shouldn't be leaking any information about the existence
            # of users because if they are querying for a user that is not
            # themselves a PERMISSION_DENIED has already been returned.
            #
            # This case should really only happen when a user with the
            # 'mozreview.modify_ldap.association' is querying for a user
            # and they are allowed to know all user existence.
            return DOES_NOT_EXIST

        return 200, self.create_item_payload(request, user, get_profile(user))

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    def get_list(self, request, *args, **kwargs):
        """Handle retrieving the list resource.

        Never return any useful information as getting the RB pagination
        to work with a non model resource is tough and not worth the effort
        at the moment. Even though we don't give useful infromation, allowing
        GET on the list resource means the RBTools API can retrieve it and
        call `list.get_item()`.
        """
        if not self.has_list_access_permissions(request, *args, **kwargs):
            return PERMISSION_DENIED

        return 200, {
            'links': self.get_links(self.list_child_resources, request=request,
                                    *args, **kwargs),
            'total_results': 0,
            self.list_result_key: [],
        }

    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'ldap_username': {
                'type': six.text_type,
                'description': 'LDAP username to associate with this user',
            },
        },
    )
    def update(self, request, ldap_username, *args, **kwargs):
        """Associate an ldap username with a user.

        The only users authorized to perform this operation are those with
        the `mozreview.modify_ldap_association` permission. Users are *not*
        allowed to update their own ldap_username association as it
        represents that the Review Board user has been proven to own the ldap
        account.
        """
        logger.info('Request to update ldap association made by user: %s' % (
                    request.user.id))
        if not request.user.has_perm('mozreview.modify_ldap_association'):
            logger.info('Could not update ldap association: permission '
                        'denied for user: %s' % (request.user.id))
            return PERMISSION_DENIED

        try:
            user = resources.user.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            logger.info('Could not update ldap association: target user %s '
                        'does not exist.' % (user))
            return DOES_NOT_EXIST

        mozreview_profile = get_profile(user)
        mozreview_profile.ldap_username = ldap_username
        mozreview_profile.save()

        logger.info('Associating user: %s with ldap_username: %s' % (user,
                    ldap_username))

        return 200, self.create_item_payload(request, user, mozreview_profile)

ldap_association_resource = LDAPAssociationResource()


class EmployeeLDAPAssociationResource(WebAPIResource):
    """Resource for updating ldap usernames for all users.

    If a Review Board user's email address is provided via the email
    field, then only that user will be updated.  Without an email
    field all users will be updated.

    Updating a user involves searching Mozilla employee's LDAP entries for
    those that match exactly either the 'mail' or 'bugzillaEmail' attributes.
    When a single match is found, the association between Review Board and
    LDAP is created or updated.
    """

    name = 'employee_ldap_association'
    allowed_methods = ('GET', 'POST',)

    def has_access_permissions(self, request, *args, **kwargs):
        return request.user.is_authenticated() and (
            request.user.has_perm('mozreview.modify_ldap_association'))

    def has_list_access_permissions(self, request, *args, **kwargs):
        return request.user.is_authenticated() and (
            request.user.has_perm('mozreview.modify_ldap_association'))

    @webapi_login_required
    @webapi_response_errors(NOT_LOGGED_IN, PERMISSION_DENIED, DOES_NOT_EXIST)
    @webapi_request_fields(
        optional={
            'email': {
                'type': six.text_type,
                'description': 'Only update this user instead of all users.',
            }
        }
    )
    def create(self, request, email='', *args, **kwargs):
        if not request.user.has_perm('mozreview.modify_ldap_association'):
            logger.info('Could not update ldap association: permission '
                        'denied for user: %s' % (request.user.id))
            return PERMISSION_DENIED

        ldap_connection = get_ldap_connection()
        if not ldap_connection:
            raise Exception('Failed to connect to LDAP')

        result = {
            'links': self.get_links(self.list_child_resources,
                                    obj=True, request=request),
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        if email:
            verbose_logging = True
            try:
                user_ids = [User.objects.get(email=email).id]
            except ObjectDoesNotExist:
                logger.info('Could not update ldap association: target user '
                            '%s does not exist.' % email)
                return DOES_NOT_EXIST

        else:
            # This is designed to be run from cron, so there's minimal logging
            # and results.
            verbose_logging = False
            user_ids = MozReviewUserProfile.objects.values_list('user_id',
                                                                flat=True)

        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                ldap_username, updated = associate_employee_ldap(
                    user, ldap_connection)

                # When called for a single user, return the ldap_username.
                if email:
                    result['ldap_username'] = [ldap_username]

                if updated:
                    result['updated'] = result['updated'] + 1

                else:
                    result['skipped'] = result['skipped'] + 1
                    if verbose_logging:
                        logging.info(
                            'Associating user: %s already associated with '
                            'ldap_username: %s' % (user.email, ldap_username))

            except LDAPAssociationException as e:
                result['errors'] = result['errors'] + 1
                if verbose_logging:
                    logger.info('Could not update ldap association: %s'
                                % str(e))

        return 200, result

employee_ldap_association_resource = EmployeeLDAPAssociationResource()
