# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cgi import escape
import ConfigParser
import os
import sys
import re
import shlex
from subprocess import (
    Popen,
    PIPE,
    STDOUT,
)

from ldap_helper import (
    get_ldap_attribute,
    get_ldap_settings,
)
import repo_group
from sh_helper import (
    prompt_user,
    run_command,
)

HG = '/repo/hg/venv_pash/bin/hg'

USER_REPO_EXISTS = """
You already have a repo called %s.

If you think this is wrong, please file a Developer Services :: hg.mozilla.org
bug at https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
""".strip()

NO_SOURCE_REPO = """
Sorry, there is no source repo called %s.

If you think this is wrong, please file a Developer Services :: hg.mozilla.org
bug at https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
""".strip()

HGWEB_ERROR = """
Problem opening hgweb.wsgi file.

Please file a Developer Services :: hg.mozilla.org bug at
https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
""".strip()

MAKING_REPO = """
Making repo {repo} for {user}.

This repo will appear as {cname}/users/{user_dir}/{repo}.

If you need a top level repo, please quit now and file a
Developer Services :: hg.mozilla.org bug at
https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
""".strip()

EDIT_DESCRIPTION = """
You are about to edit the description for hg.mozilla.org/users/%s/%s.

If you need to edit the description for a top level repo, please quit now
and file a Developer Services :: hg.mozilla.org bug at
https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
""".strip()

DOC_ROOT = '/repo/hg/mozilla'

OBSOLESCENCE_ENABLED = """
Obsolescence is now enabled for this repository.

Obsolescence is currently an experimental feature. It may be disabled at any
time. Your obsolescence data may be lost at any time. You have been warned.

Enjoy living on the edge.
""".strip()


def is_valid_user(mail):
    url = get_ldap_settings()['url']

    mail = mail.strip()
    replacements = {
        '(': '',
        ')': '',
        "'": '',
        '"': '',
        ';': '',
    }
    for search, replace in replacements.items():
        mail = mail.replace(search, replace)
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


def run_hg_clone(user_repo_dir, repo_name, source_repo_path, verbose=False):
    userdir = "%s/users/%s" % (DOC_ROOT, user_repo_dir)
    dest_dir = "%s/%s" % (userdir, repo_name)
    dest_url = "/users/%s/%s" % (user_repo_dir, repo_name)

    if os.path.exists(dest_dir):
        print(USER_REPO_EXISTS % repo_name)
        sys.exit(1)

    if (not os.path.exists('%s/%s' % (DOC_ROOT, source_repo_path)) or
            not check_repo_name(source_repo_path)):
        print(NO_SOURCE_REPO % source_repo_path)
        sys.exit(1)

    if not os.path.exists(userdir):
        run_command('mkdir %s' % userdir)
    print 'Please wait.  Cloning /%s to %s' % (source_repo_path, dest_url)
    if(verbose):
        run_command('nohup %s clone --debug --verbose --time --pull -U %s/%s %s' %
                    (HG, DOC_ROOT, source_repo_path, dest_dir),
                    verbose=True)
    else:
        run_command('nohup %s clone --pull -U %s/%s %s' %
                    (HG, DOC_ROOT, source_repo_path, dest_dir))

    print "Clone complete."


def run_repo_push(args):
    """Run repo-push.sh, signaling mirror-pull on mirrors to do something."""
    command = '/usr/bin/sudo -u hg /usr/local/bin/repo-push.sh %s' % args
    return run_command(command)


def make_wsgi_dir(cname, user_repo_dir):
    wsgi_dir = "/repo/hg/webroot_wsgi/users/%s" % user_repo_dir
    # Create user's webroot_wsgi folder if it doesn't already exist
    if not os.path.isdir(wsgi_dir):
        os.mkdir(wsgi_dir)

    print "Creating hgweb.config file"
    # Create hgweb.config file if it doesn't already exist
    if not os.path.isfile("%s/hgweb.config" % wsgi_dir):
        hgconfig = open("%s/hgweb.config" % wsgi_dir, "w")
        hgconfig.write("[web]\n")
        hgconfig.write("baseurl = http://%s/users/%s\n" % (cname, user_repo_dir))
        hgconfig.write("[paths]\n")
        hgconfig.write("/ = %s/users/%s/*\n" % (DOC_ROOT, user_repo_dir))
        hgconfig.close()

    # Create hgweb.wsgi file if it doesn't already exist
    if not os.path.isfile("%s/hgweb.wsgi" % wsgi_dir):
        try:
            hgwsgi = open("%s/hgweb.wsgi" % wsgi_dir, "w")
        except Exception:
            print(HGWEB_ERROR)
            sys.exit(1)

        hgwsgi.write("#!/usr/bin/env python\n")
        hgwsgi.write("config = '%s/hgweb.config'\n" % wsgi_dir)
        hgwsgi.write("from mercurial import demandimport; demandimport.enable()\n")
        hgwsgi.write("from mercurial.hgweb import hgweb\n")
        hgwsgi.write("import os\n")
        hgwsgi.write("os.environ['HGENCODING'] = 'UTF-8'\n")
        hgwsgi.write("application = hgweb(config)\n")
        hgwsgi.close()


def fix_user_repo_perms(repo_name):
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    print "Fixing permissions, don't interrupt."
    try:
        run_command('chown %s:scm_level_1 %s/users/%s' % (user, DOC_ROOT, user_repo_dir))
        run_command('chmod g+w %s/users/%s' % (DOC_ROOT, user_repo_dir))
        run_command('chmod g+s %s/users/%s' % (DOC_ROOT, user_repo_dir))
        run_command('chown -R %s:scm_level_1 %s/users/%s/%s' % (user, DOC_ROOT, user_repo_dir, repo_name))
        run_command('chmod -R g+w %s/users/%s/%s' % (DOC_ROOT, user_repo_dir, repo_name))
        run_command('find %s/users/%s/%s -depth -type d | xargs chmod g+s' % (DOC_ROOT, user_repo_dir, repo_name))
    except Exception, e:
        print "Exception %s" % (e)


def make_repo_clone(cname, repo_name, quick_src, verbose=False, source_repo=''):
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    dest_url = "/users/%s" % user_repo_dir
    source_repo = ''
    if quick_src:
        run_hg_clone(user_repo_dir, repo_name, quick_src)
        fix_user_repo_perms(repo_name)
        # New user repositories are non-publishing by default.
        set_repo_publishing(repo_name, False)
        sys.exit(0)
        return

    print(MAKING_REPO.format(repo=repo_name, user=user, cname=cname,
                             user_dir=user_repo_dir))
    selection = prompt_user('Proceed?', ['yes', 'no'])
    if selection != 'yes':
        return

    print 'You can clone an existing public repo or a users private repo.'
    print 'You can also create an empty repository.'
    selection = prompt_user('Source repository:', ['Clone a public repository', 'Clone a private repository', 'Create an empty repository'])
    if (selection == 'Clone a public repository'):
        exec_command = "/usr/bin/find " + DOC_ROOT + " -maxdepth 3 -mindepth 2 -type d -name .hg"
        args = shlex.split(exec_command)
        p = Popen(args, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        repo_list = p.communicate()[0].split("\n")
        if repo_list:
            print "We have the repo_list"
            repo_list = map(lambda x: x.replace(DOC_ROOT + '/', ''), repo_list)
            repo_list = map(lambda x: x.replace('/.hg', ''), repo_list)
            repo_list = sorted(repo_list)
            print 'List of available public repos'
            source_repo = prompt_user('Pick a source repo:', repo_list, period=False)
    elif (selection == 'Clone a private repository'):
        source_user = raw_input('Please enter the e-mail address of the user owning the repo: ')
        valid_user = is_valid_user(source_user)
        if valid_user == True:
            source_user = source_user.replace('@', '_')
        elif valid_user == False:
            sys.stderr.write('Unknown user.\n')
            sys.exit(1)
        elif valid_user == 'Invalid Email Address':
            sys.stderr.write('Invalid Email Address.\n')
            sys.exit(1)
        source_user_path = run_command('find ' + DOC_ROOT + '/users/' + source_user + ' -maxdepth 1 -mindepth 1 -type d')
        if not source_user_path:
            print 'That user does not have any private repositories.'
            print 'Check https://' + cname + '/users for a list of valid users.'
            sys.exit(1)
        else:
            user_repo_list = run_command('find ' + DOC_ROOT + '/users/' + source_user + ' -maxdepth 3 -mindepth 2 -type d -name .hg')
            user_repo_list = map(lambda x: x.replace(DOC_ROOT + '/users/' + source_user, ''), user_repo_list)
            user_repo_list = map(lambda x: x.replace('/.hg', ''), user_repo_list)
            user_repo_list = map(lambda x: x.strip('/'), user_repo_list)
            user_repo_list = sorted(user_repo_list)
            print 'Select the users repo you wish to clone.'
            source_repo = prompt_user('Pick a source repo:', user_repo_list, period=False)
        source_repo = 'users/' + source_user + '/' + source_repo
    elif (selection == 'Create an empty repository'):
        source_repo=''
    else:
        # We should not get here
        source_repo=''
    if source_repo != '':
        print 'About to clone /%s to /users/%s/%s' % (source_repo, user_repo_dir, repo_name)
        response = prompt_user('Proceed?', ['yes', 'no'])
        if (response == 'yes'):
            print 'Please do not interrupt this operation.'
            run_hg_clone(user_repo_dir, repo_name, source_repo)
    else:
        print "About to create an empty repository at /users/%s/%s" % (user_repo_dir, repo_name)
        response = prompt_user('Proceed?', ['yes', 'no'])
        if (response == 'yes'):
            if not os.path.exists('%s/users/%s' % (DOC_ROOT, user_repo_dir)):
                try:
                    exec_command = '/bin/mkdir %s/users/%s' % (DOC_ROOT, user_repo_dir)
                    run_command(exec_command)
                except Exception, e:
                    print "Exception %s" % (e)

            run_command('/usr/bin/nohup %s init %s/users/%s/%s' % (HG, DOC_ROOT, user_repo_dir, repo_name))
            run_repo_push('-e users/%s/%s' % (user_repo_dir, repo_name))
    fix_user_repo_perms(repo_name)
    # New user repositories are non-publishing by default.
    set_repo_publishing(repo_name, False)
    sys.exit(0)


def get_and_validate_user_repo(repo_name):
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    rel_path = '/users/%s/%s' % (user_repo_dir, repo_name)
    fs_path = '%s%s' % (DOC_ROOT, rel_path)

    if not os.path.exists(fs_path):
        sys.stderr.write('Could not find repository at %s.\n' % rel_path)
        sys.exit(1)

    return fs_path


def get_user_repo_config(repo_dir):
    """Obtain a ConfigParser for a repository.

    If the hgrc file doesn't exist, it will be created automatically.
    """
    user = os.getenv('USER')
    path = '%s/.hg/hgrc' % repo_dir
    if not os.path.isfile(path):
        run_command('touch %s' % path)
        run_command('chown %s:scm_level_1 %s' % (user, path))

    config = ConfigParser.RawConfigParser()
    if not config.read(path):
        sys.stderr.write('Could not read the hgrc file for this repo\n')
        sys.stderr.write('Please file a Developer Services :: hg.mozilla.org bug\n')
        sys.exit(1)

    return path, config


def edit_repo_description(repo_name):
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    print(EDIT_DESCRIPTION % (user_repo_dir, repo_name))
    selection = prompt_user('Proceed?', ['yes', 'no'])
    if selection != 'yes':
        return

    repo_path = get_and_validate_user_repo(repo_name)
    repo_description =  raw_input('Enter a one line descripton for the repository: ')
    if repo_description == '':
        return

    repo_description = escape(repo_description)

    config_path, config = get_user_repo_config(repo_path)

    if not config.has_section('web'):
        config.add_section('web')

    config.set('web', 'description', repo_description)

    with open(config_path, 'w+') as fh:
        config.write(fh)

    run_repo_push('-e users/%s/%s --hgrc' % (user_repo_dir, repo_name))


def set_repo_publishing(repo_name, publish):
    """Set the publishing flag on a repository.

    A publishing repository turns its pushed commits into public
    phased commits. It is the default behavior.

    Non-publishing repositories have their commits stay in the draft phase
    when pushed.
    """
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    repo_path = get_and_validate_user_repo(repo_name)
    config_path, config = get_user_repo_config(repo_path)

    if not config.has_section('phases'):
        config.add_section('phases')

    value = 'True' if publish else 'False'

    config.set('phases', 'publish', value)

    with open(config_path, 'w') as fh:
        config.write(fh)

    run_repo_push('-e users/%s/%s --hgrc' % (user_repo_dir, repo_name))

    if publish:
        sys.stderr.write('Repository marked as publishing: changesets will '
            'change to public phase when pushed.\n')
    else:
        sys.stderr.write('Repository marked as non-publishing: draft '
            'changesets will remain in the draft phase when pushed.\n')


def set_repo_obsolescence(repo_name, enabled):
    """Enable or disable obsolescence support on a repository."""
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    repo_path = get_and_validate_user_repo(repo_name)
    config_path, config = get_user_repo_config(repo_path)

    if not config.has_section('experimental'):
        config.add_section('experimental')

    if enabled:
        config.set('experimental', 'evolution', 'all')
    else:
        config.remove_option('experimental', 'evolution')

    with open(config_path, 'w') as fh:
        config.write(fh)

    run_repo_push('-e users/%s/%s --hgrc' % (user_repo_dir, repo_name))

    if enabled:
        print(OBSOLESCENCE_ENABLED)
    else:
        print('Obsolescence is now disabled for this repo.')


def do_delete(repo_dir, repo_name, verbose=False):
    if verbose:
        print "Deleting..."
    run_command('rm -rf %s/users/%s/%s' % (DOC_ROOT, repo_dir, repo_name))
    run_repo_push('-d -e users/%s/%s' % (repo_dir, repo_name))
    if verbose:
        print "Finished deleting"
    purge_log = open('/tmp/pushlog_purge.%s' % os.getpid(), "a")
    purge_log.write('echo users/%s/%s\n' % (repo_dir, repo_name))
    purge_log.close()


def delete_repo(cname, repo_name, do_quick_delete, verbose=False):
    user = os.getenv('USER')
    user_repo_dir = user.replace('@', '_')
    url_path = "/users/%s" % user_repo_dir
    if os.path.exists('%s/users/%s/%s' % (DOC_ROOT, user_repo_dir, repo_name)):
        if do_quick_delete:
            do_delete(user_repo_dir, repo_name, verbose)
        else:
            print '\nAre you sure you want to delete /users/%s/%s?' % (user_repo_dir, repo_name)
            print '\nThis action is IRREVERSIBLE.'
            selection = prompt_user('Proceed?', ['yes', 'no'])
            if (selection == 'yes'):
                do_delete(user_repo_dir, repo_name, verbose)
    else:
        sys.stderr.write('Could not find the repository at /users/%s/%s.\n' % (user_repo_dir, repo_name))
        sys.stderr.write('Please check the list at https://%s/users/%s\n' % (cname, user_repo_dir))
        sys.exit(1)
    sys.exit(0)


def edit_repo(cname, repo_name, do_quick_delete):
    if do_quick_delete:
        delete_repo(cname, repo_name, do_quick_delete)
    else:
        action = prompt_user('What would you like to do?', [
            'Delete the repository',
            'Edit the description',
            'Mark repository as non-publishing',
            'Mark repository as publishing',
            'Enable obsolescence support (experimental)',
            'Disable obsolescence support',
            ])
        if action == 'Edit the description':
            edit_repo_description(repo_name)
        elif action == 'Delete the repository':
            delete_repo(cname, repo_name, False)
        elif action == 'Mark repository as non-publishing':
            set_repo_publishing(repo_name, False)
        elif action == 'Mark repository as publishing':
            set_repo_publishing(repo_name, True)
        elif action == 'Enable obsolescence support (experimental)':
            set_repo_obsolescence(repo_name, True)
        elif action == 'Disable obsolescence support':
            set_repo_obsolescence(repo_name, False)
    return


def serve(cname):
    ssh_command = os.getenv('SSH_ORIGINAL_COMMAND')
    if not ssh_command:
        sys.stderr.write('No interactive shells allowed here!\n')
        sys.exit(1)
    elif ssh_command.startswith('hg'):
        repo_expr = re.compile('(.*)\s+-R\s+([^\s]+\s+)(.*)')
        if repo_expr.search(ssh_command):
            [(hg_path, repo_path, hg_command)] = repo_expr.findall(ssh_command)
            if hg_command == 'serve --stdio' and check_repo_name(repo_path):
                hg_arg_string = HG + ' -R ' + DOC_ROOT + '/' + repo_path + hg_command
                hg_args = hg_arg_string.split()
                os.execv(HG, hg_args)
            else:
                sys.stderr.write("Thank you dchen! but.. I don't think so!\n")
                sys.exit(1)
    elif ssh_command.startswith('clone '):
        args = ssh_command.replace('clone', '').split()
        if check_repo_name(args[0]):
            if len(args) == 1:
                make_repo_clone(cname, args[0], None)
            elif len(args) == 2:
                if os.path.isdir('%s/%s/.hg' % (DOC_ROOT, args[1])):
                    make_repo_clone(cname, args[0], args[1])
            sys.exit(0)
        sys.stderr.write('clone usage: ssh hg.mozilla.org clone newrepo [srcrepo]\n')
        sys.exit(1)
    elif ssh_command.startswith('edit '):
        args = ssh_command.replace('edit', '',  1).split()
        if check_repo_name(args[0]):
            if len(args) == 1:
                edit_repo(cname, args[0], False)
            elif len(args) == 3 and args[1] == 'delete' and args[2] == 'YES':
                edit_repo(cname, args[0], True)
            else:
                sys.stderr.write('edit usage: ssh hg.mozilla.org edit [userrepo delete] - WARNING: will not prompt!\n')
                sys.exit(1)
    elif ssh_command.startswith('pushlog '):
        args = ssh_command.replace('pushlog', '').split()
        if check_repo_name(args[0]):
            fh = open("/repo/hg/mozilla/%s/.hg/pushlog2.db" % (args[0]), 'rb')
            sys.stdout.write(fh.read())
            fh.close()
    elif ssh_command.startswith('repo-group'):
        args = ssh_command.replace('repo-group', '').split()
        if check_repo_name(args[0]):
            print(repo_group.repo_owner(args[0]))
    elif ssh_command.startswith('repo-config '):
        args = ssh_command.split()[1:]
        repo = args[0]
        if check_repo_name(repo):
            hgrc = '/repo/hg/mozilla/%s/.hg/hgrc' % repo
            if os.path.exists(hgrc):
                with open(hgrc, 'rb') as fh:
                    sys.stdout.write(fh.read())
    else:
        sys.stderr.write('No interactive commands allowed here!\n')
        sys.exit(1)
