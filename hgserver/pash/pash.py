#! /usr/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pwd


def QuoteForPOSIX(string):
    '''quote a string so it can be used as an argument in a  posix shell

    According to: http://www.unix.org/single_unix_specification/
    2.2.1 Escape Character(Backslash)

    A backslash that is not quoted shall preserve the literal value
    of the following character, with the exception of a <newline>.

    2.2.2 Single-Quotes

    Enclosing characters in single-quotes( '' ) shall preserve
    the literal value of each character within the single-quotes.
    A single-quote cannot occur within single-quotes.

    from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/498202
    thank you google!
    '''
    return "\\'".join("'" + p + "'" for p in string.split("'"))


def process_non_root_login(user):
    # Delay import so these don't interfere with root login code path.
    from datetime import datetime
    import json
    import logging
    import sys
    import hg_helper
    import ldap_helper

    user_status = hg_helper.is_valid_user(user)
    if user_status == 2:
        sys.stderr.write('Your mercurial account has been disabled due \
                          to inactivity.\nPlease file a bug at \
                          https://bugzilla.mozilla.org (or \
                          http://tinyurl.com/njcfhma) to re-activate \
                          your account.\n')
        sys.exit(0)

    elif user_status != 1:
        sys.stderr.write('You do not have a valid mercurial account!\n')
        sys.exit(0)

    # Run ldap access date toucher, silently fail and log if we're unable to write
    try:
        settings = ldap_helper.get_ldap_settings()
        ldap_helper.update_access_date(user, 'hgAccessDate',
                                       datetime.utcnow().strftime("%Y%m%d%H%M%S.%fZ"),
                                       settings['url'],
                                       settings['write_url'])
    except Exception:
         logging.basicConfig(filename='/var/log/pash.log', level=logging.DEBUG)
         logging.exception('Failed to update LDAP attributes for %s' % user)

    with open('/etc/mercurial/pash.json', 'rb') as fh:
        pash_settings = json.load(fh)

    hg_helper.serve(cname=pash_settings['hostname'])
    sys.exit(0)


if __name__ == '__main__':
    user = os.environ.get('USER')

    if user == 'root':
        root_shell = pwd.getpwuid(0)[6]
        ssh_command = os.environ.get('SSH_ORIGINAL_COMMAND')
        if ssh_command:
            os.system(root_shell + " -c " + QuoteForPOSIX(ssh_command))
        else:
            os.execl(root_shell, root_shell)
    else:
        process_non_root_login(user)
