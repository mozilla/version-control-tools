from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
from reviewboard.webapi.resources import resources, WebAPIResource
from reviewboard.webapi.resources.user import UserResource

from mozreview.models import get_profile


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
        if not request.user.has_perm('mozreview.modify_ldap_association'):
            return PERMISSION_DENIED

        try:
            user = resources.user.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        mozreview_profile = get_profile(user)
        mozreview_profile.ldap_username = ldap_username
        mozreview_profile.save()

        return 200, self.create_item_payload(request, user, mozreview_profile)


ldap_association_resource = LDAPAssociationResource()