from __future__ import unicode_literals

import logging

import ldap
from reviewboard.extensions.base import get_extension_manager


LDAP_QUERY_TIMEOUT = 5
logger = logging.getLogger(__name__)


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


def query_scm_group(username, group):
    """Return true if the user is a member of the scm group.

    For scm_* groups, the ldap users mail attribute is added
    as a memberUid of the group, so check that.

    We are cautious and will return false in cases where we
    failed to actually query ldap for the group membership.
    """
    logger.info('Querying ldap group association: %s in %s' % (
                username, group))
    l = get_ldap_connection()

    if not l:
        return False

    try:
        l.search('dc=mozilla', ldap.SCOPE_SUBTREE, filterstr='cn=%s' % group)
        result = l.result(timeout=LDAP_QUERY_TIMEOUT)

        # The memberUid attribute will only exist if there is
        # at least one member of the group.
        members = result[1][0][1].get('memberUid') or []
        in_group = username in members
        logger.info('Ldap group association: %s in %s: %s' % (
                    username, group, in_group))
        return in_group
    except ldap.LDAPError as e:
        logger.error('Failed to query ldap for group membership: %s' % e)
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
