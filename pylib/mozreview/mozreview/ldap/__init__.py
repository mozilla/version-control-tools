from __future__ import unicode_literals

import logging
import ldap

from reviewboard.extensions.base import (
    get_extension_manager,
)


LDAP_QUERY_TIMEOUT = 5
logger = logging.getLogger(__name__)


class LDAPAssociationException(Exception):
    pass


def get_ldap_connection():
    """Return an ldap connection.

    `None` will be returned if a connection cannot be made for
    any reason.
    """
    ext = get_extension_manager().get_enabled_extension(
        'mozreview.extension.MozReviewExtension')
    url = ext.get_settings('ldap_url')
    user = ext.get_settings('ldap_user')
    password = ext.get_settings('ldap_password')

    if any([not url, not user, not password]):
        logger.error("MozReview ldap support configured incorrectly.")
        return None

    try:
        c = ldap.initialize(url)
        c.simple_bind_s(user, password)
    except ldap.LDAPError as e:
        logger.error('Failed to connect to ldap: %s' % e)
        return None

    return c


def query_scm_group(username, group, ldap_connection=None):
    """Return true if the user is a member of the scm group.

    For scm_* groups, the ldap users mail attribute is added
    as a memberUid of the group, so check that.

    When a user's access expires they are not actually removed from the scm_*
    group; instead they are added to an expired_scm_* group.  For sanity
    there's a set of active_scm_* which provides real group membership.

    We are cautious and will return false in cases where we
    failed to actually query ldap for the group membership.
    """

    ldap_connection = ldap_connection or get_ldap_connection()
    if not ldap_connection:
        return False

    try:
        ldap_connection.search('dc=mozilla', ldap.SCOPE_SUBTREE,
                               filterstr='cn=active_%s' % group)
        result = ldap_connection.result(timeout=LDAP_QUERY_TIMEOUT)

        # The member attribute will only exist if there is
        # at least one member of the group.
        members = result[1][0][1].get('member') or []

        # `members` contains the DN of the user, which we don't have.
        # Because the mail attribute is unique across ldap (it's what's used
        # as the `memberUid` in `scm_level_*` groups, just checking that
        # a DN start with `mail=$user,` is sufficient.
        return any(m.startswith('mail=%s,' % username) for m in members)
    except ldap.LDAPError as e:
        logger.error('Failed to query ldap for group membership: %s' % e)
        return False


def user_exists(username, ldap_connection=None):
    """Returns true if a user exists in LDAP (MoCo, MoFo, or contrib)."""

    ldap_connection = ldap_connection or get_ldap_connection()
    if not ldap_connection:
        raise Exception('Failed to connect to LDAP')

    escaped = ldap.filter.escape_filter_chars(username)

    try:
        for org in ('com', 'org', 'net'):  # MoCo, MoFo, contributors.
            try:
                results = ldap_connection.search_ext_s(
                    'o=%s,dc=mozilla' % org,
                    ldap.SCOPE_SUBTREE,
                    '(mail=%s)' % escaped,
                    [b'mail'],
                    timeout=LDAP_QUERY_TIMEOUT)
                if results:
                    return True
            except ldap.NO_SUCH_OBJECT:
                # Ignore errors about invalid bases.
                pass
        # User not found.
        return False
    except ldap.LDAPError as e:
        logger.error('Failed to query ldap for user: %s' % e)
        return False


def find_employee_ldap(address, ldap_connection=None):
    """Find matching Mozilla employees.

    For the given email address, return a matching Mozilla employee's
    LDAP address (if found).  Both the mail and bugzillaEmail LDAP
    attributes will be checked.
    """

    try:
        if not ldap_connection:
            ldap_connection = get_ldap_connection()

        escaped = ldap.filter.escape_filter_chars(address)
        results = ldap_connection.search_ext_s(
            'o=com,dc=mozilla',
            ldap.SCOPE_SUBTREE,
            '(|(bugzillaEmail=%s)(mail=%s))' % (escaped, escaped),
            [b'mail'],
            timeout=LDAP_QUERY_TIMEOUT)

        matches = []
        for result in results:
            matches.append(result[1]['mail'][0])

        return matches
    except ldap.LDAPError:
        logger.exception('Failed to query ldap for employee address')
        return None


def associate_employee_ldap(user, ldap_connection=None):
    """Assoicate the user if we find them in the employee LDAP scope.

    For the given user object, find a matching Mozilla employee's
    LDAP address (both the mail and bugzillaEmail LDAP attributes will be
    checked), and associate the user to LDAP.

    Raises an exception if no matches or multiple matches were found.
    Returns the found LDAP username, and a boolean indicating if the user
    was updated.
    """

    from mozreview.models import get_profile
    mozreview_profile = get_profile(user)

    # Don't overwrite existing and valid associations.
    if mozreview_profile.ldap_username and user_exists(
            mozreview_profile.ldap_username, ldap_connection):
        return mozreview_profile.ldap_username, False

    ldap_users = find_employee_ldap(user.email, ldap_connection)

    if not ldap_users:
        raise LDAPAssociationException(
            'Failed to find match for %s' % user.email)

    if len(ldap_users) > 1:
        raise LDAPAssociationException(
            'More than one match for %s' % user.email)

    ldap_username = ldap_users[0]
    updated = False
    if mozreview_profile.ldap_username != ldap_username:
        if mozreview_profile.ldap_username:
            logging.info("Existing ldap association '%s' replaced by '%s'"
                         % (mozreview_profile.ldap_username, ldap_username))
        else:
            logging.info('Associating user: %s with ldap_username: %s'
                         % (user.email, ldap_username))

        mozreview_profile.ldap_username = ldap_username
        mozreview_profile.save()
        updated = True

    return ldap_username, updated
