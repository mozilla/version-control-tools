# Copyright (C) 2010 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
bzexport

Attach a patch from a HG repository to a bugzilla bug.

To enable this extension, edit your ~/.hgrc (or %APPDATA%/Mercurial.ini)
and add:

    [extensions]

    bzexport = /path/to/bzexport.py

You can then use it like so:
hg bzexport [-e] [REV] [BUG|--new]

Where REV is any local revision, and BUG is a bug number on
bugzilla.mozilla.org or the option '--new' to create a new bug. The extension
is tuned to work best with MQ changesets (it can only currently work with
applied patches).

If no revision is specified, it will default to '.' (the revision your checkout
is based on). If no bug is specified, the changeset commit message will be
scanned for a bug number to use.

This extension also adds a 'newbug' command for creating a new bug without
attaching anything to it.

"""

import json
import os
import re
import sys
import urllib2
import urlparse
from cStringIO import StringIO

from mercurial.i18n import _
from mercurial import cmdutil, util, patch
from hgext import mq

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

import bzauth
import bz

# This is stolen from buglink.py
bug_re = re.compile(r'''# bug followed by any sequence of numbers, or
                        # a standalone sequence of numbers
                     (
                        (?:
                          bug |
                          b= |
                          # a sequence of 5+ numbers preceded by whitespace
                          (?=\b\#?\d{5,}) |
                          # numbers at the very beginning
                          ^(?=\d)
                        )
                        (?:\s*\#?)(\d+)
                     )''', re.I | re.X)
review_re = re.compile(r'[ra][=?]+(\w[^ ]+)')

BINARY_CACHE_FILENAME = ".bzexport.cache"
INI_CACHE_FILENAME = ".bzexport"


def get_default_version(ui, api_server, product):
    c = bzauth.load_configuration(ui, api_server, BINARY_CACHE_FILENAME)
    versions = c['product'].get(product, {}).get('version')
    if not versions:
        raise util.Abort(_("Product %s has no versions") % product)
    # Ugh! /configuration returns the versions in sorted order, which makes it
    # impossible to determine the default. If there's something like
    # "unspecified" in the list, prefer that for now, until bzapi gets fixed.
    # https://bugzilla.mozilla.org/show_bug.cgi?id=723170
    uns = [v for v in versions if v.startswith("un")]
    return uns[-1] if uns else versions[-1]


# ui.promptchoice only allows single-character responses and was changed in
# 2.7.1 to not be backwards compatible. So ignore it completely and just use
# ui.prompt.
def prompt_manychoice(ui, message, prompts):
    while True:
        choice = ui.prompt(message, default='default')
        if choice == 'default':
            return 0
        choice = '&' + choice
        if choice in prompts:
            return prompts.index(choice)
        ui.write("unrecognized response\n")


def prompt_menu(ui, name, values,
                readable_values=None,
                message='',
                allow_none=False):
    if message and not message.endswith('\n'):
        message += "\n"
    prompts = []
    for i in range(0, len(values)):
        prompts.append("&" + str(i + 1))
        value = (readable_values or values)[i]
        message += "  %d. %s\n" % ((i + 1), value.encode('utf-8', 'replace'))
    if allow_none:
        prompts.append("&n")
        message += "  n. None\n\n"
    prompts.append("&a")
    message += "  a. Abort\n\n"
    message += _("Select %s:") % name

    choice = prompt_manychoice(ui, message, prompts)

    if allow_none and choice == len(prompts) - 2:
        return None
    if choice == len(prompts) - 1:
        raise util.Abort("User requested abort while choosing %s" % name)
    return values[choice]


def filter_strings(collection, substring):
    substring = substring.lower()
    ret = [s for s in collection if s.lower() == substring]
    return ret or [v for v in collection if v.lower().find(substring) != -1]


def choose_value(ui, desc, options, message="", usemenu=True):
    if len(options) == 0:
        return None
    elif len(options) == 1:
        return options.pop()
    elif usemenu:
        return prompt_menu(ui, desc, list(options), message=message)
    return None


def multi_user_prompt(ui, desc, search_results):
    return prompt_menu(ui, desc, search_results['names'],
                       readable_values=search_results['real_names'],
                       message="Multiple bugzilla users matching \"%s\":\n\n" % search_results["search_string"],
                       allow_none=True)


# Returns [ { search_string: original, names: [ str ], real_names: [ str ] } ]
def find_users(ui, api_server, user_cache_filename, auth, search_strings):
    c = bzauth.load_user_cache(ui, api_server, user_cache_filename)
    section = api_server

    search_results = []
    for search_string in search_strings:
        name = c.get(section, search_string)
        if name:
            search_results.append({"search_string": search_string,
                                   "names": [name],
                                   "real_names": ["not_a_real_name"]})
            continue

        try:
            try:
                users = bz.find_users(auth, search_string)
            except Exception as e:
                raise util.Abort(e.message)
            name = None
            real_names = map(lambda user: "%s <%s>" % (user["real_name"], user["email"])
                             if user["real_name"] else user["email"], users["users"])
            names = map(lambda user: user["name"], users["users"])
            search_results.append({"search_string": search_string,
                                   "names": names,
                                   "real_names": real_names})
            if len(real_names) == 1:
                c.set(section, search_string, names[0])
        except Exception, e:
            search_results.append({"search_string": search_string,
                                   "error": str(e),
                                   "real_names": None})
            raise
    bzauth.store_user_cache(c, user_cache_filename)
    return search_results


# search_strings is a simple list of strings
def validate_users(ui, api_server, auth, search_strings, multi_callback, multi_desc):
    search_results = find_users(ui, api_server, INI_CACHE_FILENAME, auth, search_strings)
    search_failed = False
    results = {}
    for search_result in search_results:
        if search_result["real_names"] is None:
            ui.write_err("Error: couldn't find user with search string \"%s\": %s\n" %
                         (search_result["search_string"], search_result["error"]))
            search_failed = True
        elif len(search_result["real_names"]) > 10:
            ui.write_err("Error: too many bugzilla users matching \"%s\":\n\n" % search_result["search_string"])
            for real_name in search_result["real_names"]:
                ui.write_err("  %s\n" % real_name.encode('ascii', 'replace'))
            search_failed = True
        elif len(search_result["real_names"]) > 1:
            user = multi_callback(ui, multi_desc, search_result)
            if user is not None:
                results[search_result['search_string']] = [user]
        elif len(search_result["real_names"]) == 1:
            results[search_result['search_string']] = search_result['names']
        else:
            ui.write_err("Couldn't find a bugzilla user matching \"%s\"!\n" % search_result["search_string"])
            search_failed = True
    return None if search_failed else results


def select_users(valid, keys):
    if valid is None:
        return None
    users = []
    for key in keys:
        users.extend(valid[key])
    return users


# Copied from savecommitmessage in localrepo.py (but with variable filename and unicode)
def savefile(repo, basename, text):
    fp = repo.opener(basename, 'wb')
    try:
        fp.write(text.encode('utf-8'))
    finally:
        fp.close()
    return repo.pathto(fp.name[len(repo.root) + 1:])

# Sure sign of a poor developer: they implement their own half-assed, one-off
# templating engine instead of reusing an existing one.

# Simple templating engine: scan a template for @KEYWORDS@ (keywords surrounded
# in @ signs). First, replace them with corresponding values in the 'fields'
# dictionary and show the result to the user. Allow user to edit. Then convert
# the whole template into a regex with /(.*?)/ in place of each keyword and
# match the edited output against that. Pull out the possibly-updated field
# values.
templates = {'new_both_template': '''Title: @BUGTITLE@
Product: @PRODUCT@
Component: @COMPONENT@
Version: @PRODVERSION@
CC: @CC@
Depends: @DEPENDS@
Blocks: @BLOCKS@

Bug Description (aka comment 0):

@BUGCOMMENT0@

--- END Bug Description ---

Attachment Filename: @ATTACHMENT_FILENAME@
Attachment Description: @ATTACHMENT_DESCRIPTION@
Reviewers: @REVIEWERS@
Feedback: @FEEDBACK@
Attachment Comment (appears as a regular comment on the bug):

@ATTACHCOMMENT@

---- END Attachment Comment ----
''',
             'new_bug_template': '''Title: @BUGTITLE@
Product: @PRODUCT@
Component: @COMPONENT@
Version: @PRODVERSION@
CC: @CC@
Depends: @DEPENDS@
Blocks: @BLOCKS@

Bug Description (aka comment 0):

@BUGCOMMENT0@

--- END Bug Description ---
''',
             'existing_bug_template': '''Bug: @BUGNUM@

Attachment Filename: @ATTACHMENT_FILENAME@
Attachment Description: @ATTACHMENT_DESCRIPTION@
Reviewers: @REVIEWERS@
Feedback: @FEEDBACK@
Attachment Comment (appears as a regular comment on the bug):

@ATTACHCOMMENT@

---- END Attachment Comment ----
'''}

field_re = re.compile(r'@([^@]+)@')


def edit_form(ui, repo, fields, template_name):
    template_fields = []

    def substitute_field(m):
        field_name = m.group(1)
        template_fields.append(field_name)
        value = fields[field_name]
        if not value:
            return '<none>'
        elif isinstance(value, list):
            return ', '.join(value)
        return value

    # Fill in a template with the passed-in fields
    template = templates[template_name]
    orig = field_re.sub(substitute_field, template)

    # Convert "template with @KEYWORD1@ and @KEYWORD2@" into "template with
    # (.*?) and (.*?)". But also allow simple fields (eg "Product: @PRODUCT@")
    # to have the space after the colon omitted, to handle the case where you
    # set a default for the field in your .hgrc and you want to clear it out
    # and be prompted instead. (The regex will end up being /Product\: *(.*?)/s
    # instead.)
    pattern = template
    pattern = re.sub(r'[^\w@]', lambda m: '\\' + m.group(0), pattern)
    pattern = re.sub(r'\\:\\ ', '\\: *', pattern)
    pattern = field_re.sub('(.*?)', pattern)
    pattern = re.compile(pattern, re.S)

    # Allow user to edit the form
    new = ui.edit(orig.encode('utf-8'), ui.username()).decode('utf-8')

    saved = savefile(repo, "last_bzexport.txt", new)
    ui.write("saved edited form in %s\n" % saved)

    # Use the previously-created pattern to pull out the new keyword values
    m = pattern.match(new)
    if not m:
        raise util.Abort("Edited form %s has invalid format" % saved)

    new_fields = fields.copy()
    marker_found = False
    for field, value in zip(template_fields, m.groups()):
        if value == '<required>':
            raise util.Abort("Required field %s not filled in" % (field,))
        elif value == '<none>' or value == '':
            if isinstance(fields[field], list):
                new_fields[field] = []
            else:
                new_fields[field] = None
        else:
            if value == '<choose-from-menu>':
                marker_found = True
                new_fields[field] = value
            else:
                if isinstance(fields[field], list):
                    new_fields[field] = re.split(', *', value)
                else:
                    new_fields[field] = value

    if new == orig and not marker_found:
        if ui.prompt(_("No changes made; continue with current values (y/n)?")) != 'y':
            sys.exit(0)

    return new_fields


def bugzilla_info(ui, profile):
    api_server = ui.config("bzexport", "api_server", "https://api-dev.bugzilla.mozilla.org/latest/")
    bugzilla = ui.config("bzexport", "bugzilla", "https://bugzilla.mozilla.org/")

    # The [bzexport] auth config entries are deprecated in favor of
    # [bugzilla] via mozhg.auth.
    username = ui.config("bzexport", "username", None)
    password = ui.config("bzexport", "password", None)

    if username:
        ui.warn('(the bzexport.username config option is deprecated and ignored; '
            'use bugzilla.username instead)\n')

    if password:
        ui.warn('(the bzexport.password config option is deprecated and ignored; '
            'use bugzilla.password or cookie auth by logging into Bugzilla in Firefox)\n')

    auth = bzauth.get_auth(ui, bugzilla, profile)
    return auth, api_server, bugzilla


def urlopen(ui, req):
    """Wraps urllib2.urlopen() to provide error handling."""
    ui.progress('Accessing bugzilla server', None, item=req.get_full_url())
    #ui.debug("%s %s\n" % (req.get_method(), req.get_data()))
    try:
        return urllib2.urlopen(req, timeout=30)
    except urllib2.HTTPError, e:
        msg = ''
        try:
            err = json.load(e)
            msg = err['message']
        except:
            msg = e
            pass

        if msg:
            ui.warn('Error: %s\n' % msg)
        raise


def infer_arguments(ui, repo, args, opts):
    '''Try to figure out which argument is a revision and which is a bug number'''
    rev = bug = None
    if len(args) < 2:
        # We need to guess at some args.
        if len(args) == 1:
            # Just one arg. Could be a revision or a bug number.

            if args[0].isdigit() and len(args[0]) <= 8:
                # If it a short numeric value, assume a bug number (even if it
                # happens to match the beginning part of a revision). bzexport
                # doesn't support using revision *numbers*. This only allows
                # for 99 million bugs.
                bug = args[0]
                ui.debug("interpreting numeric %s as a bug number" % bug)
            elif args[0] in repo:
                # Now it could be a bugzilla bug alias or a revision. If it is
                # in the repo, it's almost certainly a revision. (This covers
                # revision hashes as well as branches and 'tip' etc.)
                rev = args[0]
                ui.debug("interpreting '%s' as a revision since it is in the repo" % rev)
            elif hasattr(repo, 'mq') and args[0] in repo.mq.series:
                # If it matches the name of an mq patch, it's a revision.
                # Applied patches will have already been found in the repo, but
                # unapplied patches will be found here.
                rev = args[0]
                ui.debug("interpreting '%s' as an (unapplied) mq patch")
            else:
                # Assume it's a bug alias. The REST API will fail with bad bug
                # numbers.
                bug = args[0]
                ui.debug("interpreting '%s' as a bug alias. Fingers crossed.")

        # With zero args we'll guess at both, and if we fail we'll
        # fail later.
    elif len(args) > 2:
        raise util.Abort(_("Too many arguments!"))
    else:
        # Just right.
        rev, bug = args

    if rev is None:
        # Default to '.'
        rev = '.'

    # If no revision or '.' was given, complain about local changes
    if rev == '.' and not opts['force']:
        m, a, r, d = repo.status()[:4]
        if (m or a or r or d):
            raise util.Abort(_("Local changes found; refresh first!"))

    if rev in [".", "tip", "qtip", "default"]:
        # Look for a nicer name in the MQ.
        if hasattr(repo, 'mq') and repo.mq.applied:
            rev = repo.mq.applied[-1].name

    # Check for bug number in the patch filename
    if bug is None:
        m = re.match(r'bug[_\-]?(\d+)', rev)
        if m:
            bug = m.group(1)

    return (rev, bug)


def extract_bug_num_and_desc(desc):
    # Given a commit description, attempt to return a bug number (if found),
    # and the description with that bug number string removed.
    bug = None
    m = bug_re.search(desc)
    if m:
        bug = m.group(2)
        desc = desc[:m.start()] + desc[m.end():]
    return (bug, desc.strip())


def choose_prodcomponent(ui, cache, orig_product, orig_component, finalize=False):
    def canon(v):
        if not v or v == '<choose-from-menu>':
            return None
        return v

    product = canon(orig_product)
    component = canon(orig_component)

    products_info = cache.get('product', {})
    all_products = products_info.keys()

    def products_with_component_match(component):
        products = []
        for p in all_products:
            if len(filter_strings(products_info[p]['component'].keys(), component)) > 0:
                products.append(p)
        return products

    # Tricky case: components can legitimately contain '/'. If the user
    # specified such a component with no product, then we will have generated a
    # bogus list of candidate products and a bogus list of candidate components
    # (one of which is the correct one, since it contains the substring.)
    # Restrict to just that component.
    #
    # Note that using a '/' as a separator is deprecated. If you use '::',
    # there is no ambiguity.
    if component and not product:
        doublecolon = component.find('::')
        slash = component.find('/')
        if doublecolon != -1:
            product = component[0:doublecolon].rstrip()
            component = component[doublecolon + 2:].lstrip()
        elif slash != -1:
            all_components = set()
            for p in all_products:
                all_components.update(products_info[p]['component'].keys())
            if component.lower() not in [c.lower() for c in all_components]:
                product = component[0:slash].rstrip()
                component = component[slash + 1:].lstrip()

    # 'products' and 'components' will be the set of valid products/components
    # remaining after filtering by the 'product' and 'component' passed in
    products = all_products
    components = set()

    if product is None:
        if component is None:
            product = choose_value(ui, 'product', sorted(all_products),
                                   message="Possible Products:",
                                   usemenu=finalize)
            if product is not None:
                products = [product]
        else:
            # Inverted lookup: find products matching the given component (or
            # substring of a component)
            products = products_with_component_match(component)
    else:
        products = filter_strings(all_products, product)

    for p in products:
        components.update(products_info[p]['component'].keys())
    if component is not None:
        components = filter_strings(components, component)

    # Now choose a final product::component (unless finalize is false, in which
    # case if there are multiple possibilities, the passed-in value will be
    # preserved)

    if len(products) == 0:
        product = None
    elif len(products) == 1:
        product = products.pop()
    else:
        product = choose_value(ui, 'product', sorted(products),
                               message="Select from these products:",
                               usemenu=finalize)
        if product is not None:
            prodcomponents = products_info[product]['component'].keys()
            components = set(components).intersection(prodcomponents)
        else:
            product = orig_product

    if len(components) == 0:
        component = None
    elif len(components) == 1:
        component = components.pop()
    else:
        component = choose_value(ui, 'component', sorted(components),
                                 message="Select from these components:",
                                 usemenu=finalize)
        if component is None:
            component = orig_component

    return (product, component)


def fill_values(values, ui, api_server, finalize=False):
    cache = bzauth.load_configuration(ui, api_server, BINARY_CACHE_FILENAME)

    if 'PRODUCT' in values:
        values['PRODUCT'], values['COMPONENT'] = choose_prodcomponent(ui, cache, values['PRODUCT'],
                                                                      values['COMPONENT'], finalize=finalize)

    if 'PRODVERSION' in values:
        if values['PRODVERSION'] == '<default>' and values['PRODUCT'] not in [None, '<choose-from-menu>']:
            values['PRODVERSION'] = get_default_version(ui, api_server, values['PRODUCT'])
            ui.write("Using default version '%s' of product %s\n" %
                     (values['PRODVERSION'].encode('utf-8'), values['PRODUCT'].encode('utf-8')))

    # 'finalize' means we need the final values. (finalize will be set to false
    # for prepopulating fields that will be displayed in a form)
    if not finalize:
        return values

    if 'BUGTITLE' in values:
        if values['BUGTITLE'] in [None, '<required>']:
            values['BUGTITLE'] = ui.prompt(_("Bug title:"), default='')

    if 'BUGCOMMENT0' in values:
        if values['BUGCOMMENT0'] in [None, '<required>']:
            values['BUGCOMMENT0'] = ui.prompt(_("Bug description:"), default='')

    if 'ATTACHMENT_DESCRIPTION' in values:
        if values['ATTACHMENT_DESCRIPTION'] in [None, '<required>']:
            values['ATTACHMENT_DESCRIPTION'] = ui.prompt(_("Patch description:"), default=values['ATTACHMENT_FILENAME'])

    return values


def update_patch(ui, repo, rev, bug, update_patch, rename_patch, interactive):
    q = repo.mq
    try:
        rev = q.lookup(rev)
    except util.error.Abort:
        # If the patch is not coming from mq, don't complain that the name is not found
        update_patch = False
        rename_patch = False

    todo = []
    if rename_patch:
        todo.append("name")
    if update_patch:
        todo.append("description")
    if todo:
        if interactive and ui.prompt("Update patch " + " and ".join(todo) + " (y/n)?") != 'y':
            ui.write(_("Exiting without updating patch\n"))
            return

    if rename_patch:
        newname = str("bug-%s-%s" % (bug, re.sub(r'^bug-\d+-', '', rev)))
        if newname != rev:
            try:
                mq.rename(ui, repo, rev, newname)
            except:
                # mq.rename has a tendency to leave things in an inconsistent
                # state. Fix things up.
                q.invalidate()
                if os.path.exists(q.join(newname)) and newname not in q.fullseries:
                    os.rename(q.join(newname), q.join(rev))
                raise
            rev = newname

    if update_patch:
        # Add "Bug nnnn - " to the beginning of the description
        ph = mq.patchheader(q.join(rev), q.plainmode)
        msg = [s.decode('utf-8') for s in ph.message]
        if not msg:
            msg = ["Bug %s patch" % bug]
        elif not bug_re.search(msg[0]):
            msg[0] = "Bug %s - %s" % (bug, msg[0])
        opts = {'git': True, 'message': '\n'.join(msg).encode('utf-8'), 'include': ["re:."]}
        mq.refresh(ui, repo, **opts)

    return rev


def obsolete_old_patches(ui, auth, bugid, bugzilla, filename, ignore_id, pre_hook=None):
    try:
        bug_attachments = bz.get_attachments(auth, bugid)
        attachments = bug_attachments['bugs'][bugid]
    except Exception as e:
        raise util.Abort(e.message)

    patches = [p for p in attachments
               if (p["is_patch"]
                   and not p["is_obsolete"]
                   and p["file_name"] == filename
                   and int(p["id"]) != int(ignore_id))]
    if not patches:
        return True

    for p in patches:
        #TODO: "?last_change_time=" + p["last_change_time"] to avoid conflicts?
        attachment_url = urlparse.urljoin(bugzilla, "attachment.cgi?id=%s" % (p['id']))
        if pre_hook and not pre_hook(url=attachment_url, filename=p['file_name'], description=p["description"]):
            continue

        try:
            bz.obsolete_attachment(auth, p)
        except Exception as e:
            raise util.Abort(e.message)

    return True


def find_reviewers(ui, api_server, user_cache_filename, auth, search_strings):
    cache = bzauth.load_user_cache(ui, api_server, user_cache_filename)
    section = api_server

    search_results = []
    for search_string in search_strings:
        name = cache.get(section, search_string)
        if name:
            search_results.append({"search_string": search_string,
                                   "names": [name],
                                   "real_names": ["not_a_real_name"]})
            continue

        try:
            try:
                users = bz.find_users(auth, search_string)
            except Exception as e:
                raise util.Abort(e.message)
            name = None
            real_names = map(lambda user: "%s <%s>" % (user["real_name"], user["email"])
                             if user["real_name"] else user["email"], users["users"])
            names = map(lambda user: user["name"], users["users"])
            search_results.append({"search_string": search_string,
                                   "names": names,
                                   "real_names": real_names})
            if len(real_names) == 1:
                cache.set(section, search_string, names[0])
        except Exception, e:
            search_results.append({"search_string": search_string,
                                   "error": str(e),
                                   "real_names": None})
            raise
    bzauth.store_user_cache(cache, user_cache_filename)
    return search_results


def flag_type_id(ui, api_server, config_cache_filename, flag_name, product, component):
    """
    Look up the numeric type id for the 'review' flag from the given bugzilla server
    """
    configuration = bzauth.load_configuration(ui, api_server, config_cache_filename)
    if not configuration or not configuration["flag_type"]:
        raise util.Abort(_("Could not find configuration object"))

    # Get the set of flag ids used for this product::component
    prodflags = configuration['product'][product]['component'][component]['flag_type']
    flagdefs = configuration['flag_type']

    flag_ids = [id for id in prodflags if flagdefs[str(id)]['name'] == flag_name]

    if len(flag_ids) != 1:
        raise util.Abort(_("Could not find unique %s flag id") % flag_name)

    return flag_ids[0]


def review_flag_type_id(ui, api_server, config_cache_filename, product, component):
    return flag_type_id(ui, api_server, config_cache_filename, 'review', product, component)


def feedback_flag_type_id(ui, api_server, config_cache_filename, product, component):
    return flag_type_id(ui, api_server, config_cache_filename, 'feedback', product, component)


def create_attachment(ui, api_server, auth, bug,
                      config_cache_filename,
                      attachment_contents, description="attachment",
                      filename="attachment", comment="",
                      reviewers=None, feedback=None, product=None, component=None):

    opts = {}
    if reviewers:
        opts['review_flag_id'] = review_flag_type_id(ui, api_server, config_cache_filename, product, component)
        opts['reviewers'] = reviewers

    if feedback:
        opts['feedback_flag_id'] = feedback_flag_type_id(ui, api_server, config_cache_filename, product, component)
        opts['feedback'] = feedback

    return bz.create_attachment(auth, bug, attachment_contents,
                                description=description, filename=filename,
                                comment=comment,
                                **opts)


def bzexport(ui, repo, *args, **opts):
    """
    Export changesets to bugzilla attachments.

    The -e option may be used to bring up an editor that will allow editing all
    fields of the attachment and bug (if creating one).

    The --new option may be used to create a new bug rather than using an
    existing bug. See the newbug command for details.

    The -u (--update) option is equivalent to setting both 'update-patch'
    and 'rename-patch' to True in the [bzexport] section of your config file.
    """
    auth, api_server, bugzilla = bugzilla_info(ui, opts.get('ffprofile'))

    rev, bug = infer_arguments(ui, repo, args, opts)

    if not opts['new']:
        for o in ('cc', 'depends', 'blocks'):
            if opts[o]:
                ui.write("Warning: ignoring --%s option when not creating a bug\n" % o)

    contents = StringIO()
    diffopts = patch.diffopts(ui, opts)
    context = ui.config("bzexport", "unified", None)
    if context:
        diffopts.context = int(context)
    if rev in repo:
        description_from_patch = repo[rev].description().decode('utf-8')
        if hasattr(cmdutil, "export"):
            cmdutil.export(repo, [rev], fp=contents, opts=diffopts)
        else:
            # Support older hg versions
            patch.export(repo, [rev], fp=contents, opts=diffopts)
    else:
        q = repo.mq
        contents = q.opener(q.lookup(rev), "r")
        description_from_patch = '\n'.join(mq.patchheader(q.join(rev), q.plainmode).message)

    # Just always use the rev name as the patch name. Doesn't matter much,
    # unless you want to avoid obsoleting existing patches when uploading a
    # version that doesn't include whitespace changes.
    filename = rev
    if opts['ignore_all_space']:
        filename += "_ws"

    patch_comment = None
    reviewers = []
    orig_desc = opts['description'] or description_from_patch
    if not orig_desc or orig_desc.startswith('[mq]'):
        desc = '<required>'
    else:
        # Lightly reformat changeset messages into attachment descriptions.
        # Only use the first line of the provided description for our actual
        # description - use the rest for the patch/bug comment.
        parts = orig_desc.split('\n', 1)
        firstline = parts[0]
        if len(parts) == 2:
            patch_comment = parts[1].strip()

        # Attempt to split the firstline into a bug number, and strip()ed
        # description with that bug number string removed.
        desc_bug_number, desc = extract_bug_num_and_desc(firstline)

        # Failing that try looking in the commit description for a bug number,
        # since orig_desc could have come from the command line instead.
        if not desc_bug_number:
            commit_firstline = description_from_patch.split('\n', 1)[0]
            desc_bug_number, __ = extract_bug_num_and_desc(commit_firstline)

        if desc_bug_number:
            if bug and bug != desc_bug_number:
                ui.warn("Warning: Bug number %s from commandline doesn't match "
                        "bug number %s from changeset description\n"
                        % (bug, desc_bug_number))
            else:
                bug = desc_bug_number

        # Strip any remaining leading separator and whitespace,
        # if the original was something like "bug NNN - "
        if desc[0] in ['-', ':', '.']:
            desc = desc[1:].lstrip()

        # Next strip off review and approval annotations, grabbing the
        # reviewers from the patch comments only if -r auto was given
        def grab_reviewer(m):
            if opts['review'] == 'auto':
                reviewers.append(m.group(1))
            return ''
        desc = review_re.sub(grab_reviewer, desc).rstrip()

        # Strip any trailing separators, if the original was something like:
        # "Desc; r=foo" or "Desc. r=foo"
        if desc[-1] in [';', '.']:
            desc = desc[:-1].rstrip()

        if len(reviewers) > 0:
            opts['review'] = ''

    attachment_comment = opts['comment']
    bug_comment = opts['bug_description']

    if not attachment_comment:
        # New bugs get first shot at the patch comment
        if not opts['new'] or bug_comment:
            attachment_comment = patch_comment

    if not bug_comment and opts['new']:
        bug_comment = patch_comment

    if opts["review"]:
        search_strings = opts["review"].split(",")
        valid_users = validate_users(ui, api_server, auth, search_strings, multi_user_prompt, 'reviewer')
        reviewers = select_users(valid_users, search_strings)
    elif len(reviewers) > 0:
        # Pulled reviewers out of commit message
        valid_users = validate_users(ui, api_server, auth, reviewers, multi_user_prompt, 'reviewer')
        reviewers = select_users(valid_users, reviewers)

    if reviewers is None:
        raise util.Abort(_("Invalid reviewers"))

    feedback = []
    if opts["feedback"]:
        search_strings = opts["feedback"].split(",")
        valid_users = validate_users(ui, api_server, auth, search_strings, multi_user_prompt, 'feedback from')
        feedback = select_users(valid_users, search_strings)

    values = {'BUGNUM': bug,
              'ATTACHMENT_FILENAME': filename,
              'ATTACHMENT_DESCRIPTION': desc,
              'ATTACHCOMMENT': attachment_comment,
              'REVIEWERS': reviewers,
              'FEEDBACK': feedback,
              }

    cc = []
    depends = opts["depends"].split(",")
    blocks = opts["blocks"].split(",")
    if opts['new']:
        if opts["cc"]:
            search_strings = opts["cc"].split(",")
            valid_users = validate_users(ui, api_server, auth, search_strings, multi_user_prompt, 'CC')
            cc = select_users(valid_users, search_strings)

        values['BUGTITLE'] = opts['title'] or desc
        values['PRODUCT'] = opts.get('product', '') or ui.config("bzexport", "product", '<choose-from-menu>')
        values['COMPONENT'] = opts.get('component', '') or ui.config("bzexport", "component", '<choose-from-menu>')
        values['PRODVERSION'] = opts.get('prodversion', '') or ui.config("bzexport", "prodversion", '<default>')
        values['BUGCOMMENT0'] = bug_comment
        values['CC'] = cc
        values['BLOCKS'] = blocks
        values['DEPENDS'] = depends

    values = fill_values(values, ui, api_server, finalize=False)

    if opts['edit']:
        if opts['new']:
            values = edit_form(ui, repo, values, 'new_both_template')
        else:
            values = edit_form(ui, repo, values, 'existing_bug_template')
            bug = values['BUGNUM']

        search_strings = []
        for key in ('REVIEWERS', 'CC', 'FEEDBACK'):
            # TODO: Handle <choose-from-menu>
            search_strings.extend(values.get(key, []))
        users = validate_users(ui, api_server, auth, search_strings, multi_user_prompt, 'reviewer')
        if users is None:
            raise util.Abort("Invalid users")

        if 'REVIEWERS' in values:  # Always true
            reviewers = select_users(users, values['REVIEWERS'])
        if 'CC' in values:         # Only when opts['new']
            cc = select_users(users, values['CC'])
        if 'BLOCKS' in values:     # Only when opts['new']
            blocks = values['BLOCKS']
        if 'DEPENDS' in values:    # Only when opts['new']
            depends = values['DEPENDS']
        if 'FEEDBACK' in values:   # Always true
            feedback = select_users(users, values['FEEDBACK'])
        if 'ATTACHMENT_FILENAME' in values:
            filename = values['ATTACHMENT_FILENAME']

    values = fill_values(values, ui, api_server, finalize=True)

    if opts["new"]:
        if bug is not None:
            raise util.Abort("Bug %s given but creation of new bug requested!" % bug)

        if opts['interactive'] and ui.prompt(_("Create bug in '%s' :: '%s' (y/n)?") %
                                             (values['PRODUCT'], values['COMPONENT'])) != 'y':
            ui.write(_("Exiting without creating bug\n"))
            return

        try:
            create_opts = {}
            if not opts['no_take_bug']:
                create_opts['assign_to'] = auth.username(api_server)
            result = bz.create_bug(auth,
                                product=values['PRODUCT'],
                                component=values['COMPONENT'],
                                version=values['PRODVERSION'],
                                title=values['BUGTITLE'],
                                description=values['BUGCOMMENT0'],
                                cc=cc,
                                depends=depends,
                                blocks=blocks,
                                **create_opts)
            bug = result['id']
            ui.write("Created bug %s at %sshow_bug.cgi?id=%s\n" % (bug, bugzilla, bug))
        except Exception, e:
            raise util.Abort(_("Error creating bug: %s\n" % str(e)))
    else:
        if bug is None:
            raise util.Abort(_("No bug number specified and no bug number "
                               "listed in changeset message!"))

    if len(reviewers) > 0:
        for reviewer in reviewers:
            ui.write("Requesting review from " + reviewer + "\n")
    if len(cc) > 0:
        for user in cc:
            ui.write("CC'ing %s\n" % user)
    if len(feedback) > 0:
        for user in feedback:
            ui.write("Requesting feedback from %s\n" % user)

    if not opts['no_update']:
        if opts['update']:
            update = True
        elif opts['new']:
            update = ui.configbool("bzexport", "update-patch", True)
        else:
            update = ui.configbool("bzexport", "update-patch", False)

        if opts['update']:
            rename = opts['update']
        else:
            rename = ui.configbool("bzexport", "rename-patch", False)

        newname = update_patch(ui, repo, rev, bug, update, rename, opts['interactive'])
        if filename == rev:
            filename = newname

    if opts['interactive'] and ui.prompt(_("Attach patch (y/n)?")) != 'y':
        ui.write(_("Exiting without creating attachment\n"))
        return

    extra_args = {}
    if feedback:
        extra_args['feedback'] = feedback

    if reviewers:
        extra_args['reviewers'] = reviewers

    if feedback or reviewers:
        # Need product and component to get the right flag id
        if 'PRODUCT' in values and 'COMPONENT' in values:
            extra_args['product'] = values['PRODUCT']
            extra_args['component'] = values['COMPONENT']
        else:
            buginfo = bz.get_bug(auth, bug, include_fields=['product', 'component'])
            extra_args['product'] = buginfo['product']
            extra_args['component'] = buginfo['component']

    description = values['ATTACHMENT_DESCRIPTION']
    if opts['number']:
        description = "Patch " + opts['number'] + " - " + description

    contents.seek(0)
    result = create_attachment(ui, api_server, auth,
                               bug, BINARY_CACHE_FILENAME, contents.read(),
                               filename=filename,
                               description=description,
                               comment=values['ATTACHCOMMENT'],
                               **extra_args)
    attachid = result['attachments'].keys()[0]
    attachment_url = urlparse.urljoin(bugzilla,
                                      'attachment.cgi?id=%s&action=edit' %
                                      attachid)
    print "%s uploaded as %s" % (rev, attachment_url)

    def pre_obsolete(**kwargs):
        if not opts['interactive']:
            return True
        url, filename, description = [kwargs[k] for k in ['url', 'filename', 'description']]
        return ui.prompt(_("Obsolete patch %s (%s) - %s (y/n)?") % (url, filename, description)) == 'y'

    obsolete_old_patches(ui, auth, bug, bugzilla, filename, attachid, pre_hook=pre_obsolete)

    # If attaching to an existing bug (and not suppressed on the command line), take the bug
    if not opts['new'] and not opts['no_take_bug']:
        result = bz.get_bug(auth, bug, include_fields=['assigned_to', 'status'])
        taker = auth.username(api_server)
        if result['assigned_to_detail']['name'] != taker:
            params = {'assigned_to': taker}
            if result['status'] != 'RESOLVED':
                params['status'] = 'ASSIGNED'
            try:
                result = bz.update_bug(auth, result['id'], params)
            except Exception as e:
                raise util.Abort(e.message)


def newbug(ui, repo, *args, **opts):
    """
    Create a new bug in bugzilla

    A menu will be displayed for the product and component unless a default has
    been set in the [bzexport] section of the config file (keys are 'product'
    and 'component'), or if something has been specified on the command line.

    The -e option brings up an editor that will allow editing all handled
    fields of the bug.

    The product and/or component given on the command line or the edited form
    may be case-insensitive substrings rather than exact matches of valid
    values. Ambiguous matches will be resolved with a menu. The -C
    (--component) option may be used to set both the product and component by
    separating them with a double colon ('::'), though usually just giving the
    component should be sufficient.
    """
    auth, api_server, bugzilla = bugzilla_info(ui, opts.get('ffprofile'))

    if args:
        args = list(args)

    if args and not opts['title']:
        opts['title'] = args.pop(0)
    if args and not opts['comment']:
        opts['comment'] = args.pop(0)
    if args:
        raise util.Abort(_("Too many arguments to newbug command (only title and comment may be given)"))

    bug_comment = opts['comment'] or '<required>'

    values = {'BUGTITLE': opts['title'] or '<required>',
              'PRODUCT': opts.get('product', '') or ui.config("bzexport", "product", '<choose-from-menu>'),
              'COMPONENT': opts.get('component', '') or ui.config("bzexport", "component", '<choose-from-menu>'),
              'PRODVERSION': opts.get('prodversion', '') or ui.config("bzexport", "prodversion", '<default>'),
              'BUGCOMMENT0': bug_comment,
              'CC': [cc for cc in opts.get('cc', '').split(',') if cc],
              'DEPENDS': opts["depends"].split(","),
              'BLOCKS': opts["blocks"].split(","),
              }

    fill_values(values, ui, api_server, finalize=False)

    if opts['edit']:
        values = edit_form(ui, repo, values, 'new_bug_template')

    fill_values(values, ui, api_server, finalize=True)

    cc = validate_users(ui, api_server, auth, values['CC'], multi_user_prompt, 'reviewer')
    if cc is None:
        raise util.Abort("Invalid users")
    cc = select_users(cc, values['CC'])

    if opts['interactive'] and ui.prompt(_("Create bug in '%s' :: '%s' (y/n)?") %
                                         (values['PRODUCT'], values['COMPONENT'])) != 'y':
        ui.write(_("Exiting without creating bug\n"))
        return

    create_opts = {}
    if opts['take_bug']:
        create_opts['assign_to'] = auth.username(api_server)

    result = bz.create_bug(auth,
                        product=values['PRODUCT'],
                        component=values['COMPONENT'],
                        version=values['PRODVERSION'],
                        title=values['BUGTITLE'],
                        description=values['BUGCOMMENT0'],
                        cc=cc,
                        depends=values['DEPENDS'],
                        blocks=values['BLOCKS'],
                        **create_opts)
    bug = result['id']
    ui.write("Created bug %s at %sshow_bug.cgi?id=%s\n" % (bug, bugzilla, bug))

newbug_opts = [
    ('t', 'title', '',
     'New bug title'),
    ('', 'product', '',
     'New bug product'),
    ('C', 'component', '',
     'New bug component'),
    ('', 'prodversion', '',
     'New bug product version'),
    ('', 'cc', '',
     'List of users to CC on the bug (comma-separated search strings)'),
    ('D', 'depends', '',
     'Make new bug depend on given bug number'),
    ('B', 'blocks', '',
     'Comma-separated list of bugs that should depend on this one'),
    ('P', 'ffprofile', '',
     'Name of Firefox profile to pull bugzilla cookies from'),
]

cmdtable = {
    'bzexport':
    (bzexport,
        [('d', 'description', '', 'Bugzilla attachment description'),
         ('c', 'comment', '', 'Comment to add with the attachment'),
         ('e', 'edit', False,
          'Open a text editor to modify bug fields'),
         ('r', 'review', '',
          'List of users to request review from (comma-separated search strings),'
          'or "auto" to parse the reviewers out of the patch comment'),
         ('F', 'feedback', '',
          'List of users to request feedback from (comma-separated search strings)'),
         ('', 'cc', '',
          'List of users to CC on the bug (comma-separated search strings)'),
         ('', 'new', False,
          'Create a new bug'),
         ('i', 'interactive', False,
          'Interactive -- request confirmation before any permanent action'),
         ('', 'no-take-bug', False,
          'Do not assign bug to myself'),
         ('', 'bug-description', '',
          'New bug description (aka comment 0)'),
         ('u', 'update', None,
          'Update patch name and description to include bug number (only valid with --new)'),
         ('', 'no-update', None,
          'Suppress patch name/description update (override config file)'),
         ('', 'number', '',
          'When posting, prefix the patch description with "Patch <number> - "'),
         # The following option is passed through directly to patch.diffopts
         ('w', 'ignore_all_space', False,
          'Generate a diff that ignores whitespace changes'),
         ('f', 'force', False,
          'Proceed even if the working directory contains changes'),
         ] + newbug_opts,
        _('hg bzexport [options] [REV] [BUG]')),

    'newbug':
    (newbug,
        [('c', 'comment', '', 'Comment to add with the bug'),
         ('e', 'edit', False,
          'Open a text editor to modify bug fields'),
         ('i', 'interactive', False,
          'Interactive -- request confirmation before any permanent action'),
         ('f', 'force', False,
          'Proceed even if the working directory contains changes'),
         ('', 'take-bug', False,
          'Assign bug to myself'),
         ] + newbug_opts,
        _('hg newbug [-e] [[-t] TITLE] [[-c] COMMENT]')),
}
