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

import base64
import urllib
import urllib2
import urlparse
import json

JSON_HEADERS = {"Accept": "application/json",
                "Content-Type": "application/json"}


def make_url(api_server, auth, command, args={}):
    url = urlparse.urljoin(api_server, command)
    if auth is None and not args.keys():
        return url
    params = [auth.auth()] if auth else []
    params.extend([k + "=" + urllib.quote(str(v)) for k, v in args.iteritems()])
    return url + "?" + '&'.join(params)


def create_bug(token, product, component, version, title, description,
               assign_to=None, cc=[], depends=[], blocks=[]):
    """
    Create a bugzilla bug.
    """
    o = {
        'product': product,
        'component': component,
        'summary': title,
        'version': version,
        'description': description,
        'op_sys': 'All',
        'platform': 'All',
        'depends_on': depends,
        'blocks': blocks,
        'cc': cc,
    }

    if assign_to:
        o['assigned_to'] = assign_to
        o['status'] = 'ASSIGNED'

    return token.rest_request('POST', 'bug', data=o)


def create_attachment(auth, bug, contents,
                      description="attachment",
                      filename="attachment", comment="",
                      reviewers=None, review_flag_id=None,
                      feedback=None, feedback_flag_id=None):
    """
    Post an attachment to a bugzilla bug using BzAPI.
    """
    attachment = base64.b64encode(contents)

    o = {
        'ids': [bug],
        'data': attachment,
        'encoding': 'base64',
        'file_name': filename,
        'summary': description,
        'is_patch': True,
        'content_type': 'text/plain',
        'flags': [],
    }

    if reviewers:
        assert review_flag_id
        for requestee in reviewers:
            o['flags'].append({
                'name': 'review',
                'requestee': requestee,
                'status': '?',
                'type_id': review_flag_id,
                'new': True,
            })

    if feedback:
        assert feedback_flag_id
        for requestee in feedback:
            o['flags'].append({
                'name': 'feedback',
                'requestee': requestee,
                'status': '?',
                'type_id': feedback_flag_id,
                'new': True,
            })

    if comment:
        o['comment'] = comment

    return auth.rest_request('POST', 'bug/%s/attachment' % bug, data=o)


class PUTRequest(urllib2.Request):
    def get_method(self):
        return "PUT"


def get_attachments(auth, bug):
    return auth.rest_request('GET', 'bug/%s/attachment' % bug)


def obsolete_attachment(auth, attachment):
    o = {
        'ids': [attachment['id']],
        'is_obsolete': True,
    }
    return auth.rest_request('PUT', 'bug/attachment/%s' % attachment['id'],
        data=o)

def find_users(api_server, token, search_string):
    url = make_url(api_server, token, 'user', {'match': search_string})
    return urllib2.Request(url, None, JSON_HEADERS)


def get_user(api_server, bzauth):
    url = make_url(api_server, bzauth, 'user/%s' % bzauth._userid)
    return urllib2.Request(url, None, JSON_HEADERS)


def get_configuration(api_server):
    url = make_url(api_server, None, 'configuration', {'cached_ok': 1})
    return urllib2.Request(url, None, JSON_HEADERS)


def get_bug(api_server, token, bug, **opts):
    """
    Retrieve an existing bug
    """
    args = {}
    if 'include_fields' in opts:
        args['include_fields'] = ",".join(set(
            opts['include_fields'] + ['id', 'ref', 'token', 'last_change_time', 'update_token']))
    url = make_url(api_server, token, 'bug/%s' % str(bug), args)
    return urllib2.Request(url, None, JSON_HEADERS)


def update_bug(api_server, token, bugdata):
    """
    Update an existing bug. Must pass in an existing bug as a data structure.
    Mid-air collisions are possible.
    """
    url = make_url(api_server, token, 'bug/%s' % str(bugdata['id']))
    return PUTRequest(url, json.dumps(bugdata), JSON_HEADERS)
