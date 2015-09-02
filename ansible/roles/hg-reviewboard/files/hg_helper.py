# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import sys

from ldap_helper import (
    get_ldap_attribute,
    get_ldap_settings,
)


DOC_ROOT = '/repo/hg/mozilla'


def is_valid_user(mail):
    url = get_ldap_settings()['url']

    mail = mail.strip()
    # If the regex search below fails, comment out the conditional and the
    # return. Then Uncomment the following line to atleat sanitize the input
    mail = mail.replace("(",'').replace(")",'').replace("'",'').replace('"','').replace(';','').replace("\"",'')
    # if not re.search("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", mail):
    #     return 'Invalid Email Address'
    account_status = get_ldap_attribute(mail, 'hgAccountEnabled', url)
    if account_status == 'TRUE':
        return 1
    elif account_status == 'FALSE':
        return 2
    else:
        return 0


# Please be very careful when you relax/change the good_chars regular expression.
# Being lax with it can open us up to all kind of security problems.
def check_repo_name(repo_name):
    good_chars = re.compile('^(\w|-|/|\.\w)+\s*$')
    if not good_chars.search(repo_name):
        sys.stderr.write('Only alpha-numeric characters, ".", and "-" are allowed in the repository names.\n')
        sys.stderr.write('Please try again with only those characters.\n')
        sys.exit(1)
    return True


def serve(cname=None, **kwargs):
    ssh_command = os.environ.get('SSH_ORIGINAL_COMMAND')
    if not ssh_command:
        sys.stderr.write('No interactive shells allowed here!\n')
        sys.exit(1)
    elif ssh_command.startswith('hg'):
        repo_expr = re.compile('(.*)\s+-R\s+([^\s]+\s+)(.*)')
        if repo_expr.search(ssh_command):
            [(hg_path, repo_path, hg_command)] = repo_expr.findall(ssh_command)
            if hg_command == 'serve --stdio' and check_repo_name(repo_path):
                hg_arg_string = '/usr/bin/hg -R ' + DOC_ROOT + '/' + repo_path + hg_command
                hg_args = hg_arg_string.split()
                os.execv('/usr/bin/hg', hg_args)
            else:
                sys.stderr.write("Thank you dchen! but.. I don't think so!\n")
                sys.exit(1)
    else:
        sys.stderr.write('No interactive commands allowed here!\n')
        sys.exit(1)
