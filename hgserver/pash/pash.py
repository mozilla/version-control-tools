#!/var/hg/venv_pash/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os


NO_HG_ACCESS = '''
A SSH connection has been established and your account (%s)
was found in LDAP.

However, Mercurial access is not currently enabled on your LDAP account.

Please follow the instructions at the following URL to gain Mercurial
access:

    https://www.mozilla.org/en-US/about/governance/policies/commit/
'''.lstrip()

HG_ACCESS_DISABLED = '''
A SSH connection has been established, your account (%s)
was found in LDAP, and your account has been configured for Mercurial
access.

However, Mercurial access is currently disabled on your account.
This commonly occurs due to account inactivity (you need to SSH
into hg.mozilla.org every few months to keep your account active).

To restore Mercurial access, please file a MOC Service Request
bug (http://tinyurl.com/njcfhma) and request hg access be restored
for %s.
'''.lstrip()


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


def source_environment(path):
    """Source a file with environment variables.

    Parsed environment variables are added to ``os.environ`` as a side-effect.
    """
    if not os.path.isfile(path):
        return

    # Open in text mode because environment variables are not bytes in Python
    # 3.
    with open(path, 'r') as fh:
        for line in fh:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            # Valid formats:
            # key=value
            # key="value"
            if '=' not in line:
                continue

            key, value = line.split('=', 1)

            key = key.strip()
            value = value.strip()

            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            os.environ[key] = value


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
        sys.stderr.write(HG_ACCESS_DISABLED % (user, user))
        sys.exit(0)

    elif user_status != 1:
        sys.stderr.write(NO_HG_ACCESS % user)
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

    hg_helper.serve(cname=pash_settings['hostname'],
                    enable_repo_config=pash_settings.get('repo_config', False),
                    enable_repo_group=pash_settings.get('repo_group', False),
                    enable_user_repos=pash_settings.get('user_repos', False),
                    enable_mozreview_ldap_associate=pash_settings.get('mr_ldap_associate', False))
    sys.exit(0)


if __name__ == '__main__':
    # /etc/environment contains important environment variables needed for
    # the execution of some functionality (like hooks making HTTP requests
    # and needing to pick up http_proxy and kin). This file is normally sourced
    # by login shells. But we are the login process and a shell is never
    # invoked. There are ways to get sshd to source a file with environment
    # variables by using PAM. But this feels  complicated and requires mucking
    # about with system auth settings. It is relatively easy to source the file
    # from Python. So we do that.
    source_environment('/etc/environment')

    user = os.environ.get('USER')
    process_non_root_login(user)
