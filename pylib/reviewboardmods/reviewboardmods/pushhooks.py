"""Push commits to Review Board.

This module contains code for taking commits from version control (Git,
Mercurial, etc) and adding them to Review Board.

It is intended for this module to be generic and applicable to any
Review Board install. Please abstract away Mozilla implementation
details.
"""

from rbtools.api.client import RBClient
from rbtools.api.errors import APIError


def associate_ldap_username(url, ldap_username, privileged_username,
                            privileged_password, username, apikey):
    """Associate a Review Board user with an ldap username.

    Will return True if an ldap_username is successfully associated
    with a Review Board account, False otherwise.

    This function does not prove ownership over the provided
    ldap_username, it assumes that has been done by the caller
    (e.g. They have pushed to an ldap authenticated hg server
    over ssh).

    In order to associate an ldap username with a user two sets of
    credentials needs to be provided: A user account with permission
    to change ldap associations, and a user account to be changed
    (privileged_username/privileged_password and
    username/apikey respectively).

    The Review Board credentials of the user account to be changed
    are required since we should never associate an ldap username
    with a Review Board account unless the requester has proven
    ownership of the Review Board account.
    """
    # TODO: Provide feedback on what went wrong when we fail to
    # associate the username.

    # TODO: Figure out a better way to make sure bots don't end up
    # associating their ldap account with a Review Board user they
    # are pushing for. Bug 1176008
    if ldap_username == 'bind-autoland@mozilla.com':
        return False

    if not username or not apikey:
        return False

    try:
        # We first verify that the provided credentials are valid and
        # retrieve the username associated with that Review Board
        # account.
        rbc = ReviewBoardClient(url, username=username, apikey=apikey)
        root = rbc.get_root()
        session = root.get_session()

        if not session.authenticated:
            return False

        user = session.get_user()
        username = user.username

        # Now that we have proven ownership over the user, take the provided
        # ldap_username and associate it with the account.
        rbc = ReviewBoardClient(url, username=privileged_username,
                                password=privileged_password)
        root = rbc.get_root()
        ext = root.get_extension(
            extension_name='mozreview.extension.MozReviewExtension')
        ldap = ext.get_ldap_associations().get_item(username)
        ldap.update(ldap_username=ldap_username)

    except APIError:
        return False

    return True


def ReviewBoardClient(url, username=None, password=None, apikey=None):
    """Obtain a RBClient instance."""
    if username and apikey:
        rbc = RBClient(url, save_cookies=False, allow_caching=False)
        login_resource = rbc.get_path(
            'extensions/mozreview.extension.MozReviewExtension/'
            'bugzilla-api-key-logins/')
        login_resource.create(username=username, api_key=apikey)
    else:
        rbc = RBClient(url, username=username, password=password,
                       save_cookies=False, allow_caching=False)

    return rbc
