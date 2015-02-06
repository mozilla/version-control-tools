#! /usr/bin/python -u

import datetime, os, sys, pwd
import hg_helper, ldap_helper
import logging
from sh_helper import QuoteForPOSIX

if __name__ == '__main__':
    os.environ['PYTHONPATH'] = '/repo/hg/libraries/'
    if os.getenv ('USER') == 'root':
        root_shell = pwd.getpwuid (0)[6]
        ssh_command = os.getenv ('SSH_ORIGINAL_COMMAND')
        if ssh_command:
            os.system (root_shell + " -c " + QuoteForPOSIX (ssh_command))
        else:
            os.execl (root_shell, root_shell)
    else:
        server_port = os.getenv('SSH_CONNECTION').split ()[-1]

        user_status = hg_helper.is_valid_user(os.getenv('USER'))
        if user_status == 2:
            sys.stderr.write('Your mercurial account has been disabled due \
                              to inactivity.\nPlease file a bug at \
                              https://bugzilla.mozilla.org (or \
                              http://tinyurl.com/2aveg9k) to re-activate \
                              your account.\n')
            sys.exit(0)

        elif user_status != 1:
            sys.stderr.write('You do not have a valid mercurial account!\n')
            sys.exit(0)

        # Run ldap access date toucher, silently fail and log if we're unable to write
        try:
           ldap_helper.update_ldap_attribute(os.getenv('USER'), 'hgAccessDate', datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S.%fZ"), 'ldap://ldap.db.scl3.mozilla.com', 'ldap://ldapsync1.db.scl3.mozilla.com')
        except Exception:
           logging.basicConfig(filename='/var/log/pash.log',level=logging.DEBUG)
           logging.exception('Failed to update LDAP attributes for ' + os.getenv('USER'))

        # hg.mozilla.org handler
        if server_port == "22":
            hg_helper.serve('hg.mozilla.org')

        # hg.ecmascript.org handler
        elif server_port == "222":
            hg_helper.serve('hg.ecmascript.org')

        sys.exit (0)
