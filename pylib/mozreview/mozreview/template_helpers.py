# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from mozreview.autoland.models import AutolandRequest
from mozreview.extra_data import (
    fetch_commit_data,
    gen_child_rrs,
    get_parent_rr,
    is_parent,
)

def get_commit_table_context(request, review_request_details):
    """Get the data needed to display the commits table.

    Information provided includes the parent and child review requests,
    as well as autoland information.
    """
    commit_data = fetch_commit_data(review_request_details)

    user = request.user
    parent = get_parent_rr(review_request_details.get_review_request(), commit_data=commit_data)
    parent_details = parent.get_draft(user) or parent

    # If a user can view the parent draft they should also have
    # permission to view every child. We check if the child is
    # accessible anyways in case it has been restricted for other
    # reasons.
    children_details = [
        child for child in gen_child_rrs(parent_details, user=user)
        if child.is_accessible_by(user)]
    n_children = len(children_details)
    current_child_num = prev_child = next_child = None

    if not is_parent(review_request_details, commit_data=commit_data):
        cur_index = children_details.index(review_request_details)
        current_child_num = cur_index + 1
        next_child = (children_details[cur_index + 1]
                      if cur_index + 1 < n_children else None)
        prev_child = (children_details[cur_index - 1]
                      if cur_index - 1 >= 0 else None)

    latest_autoland_requests = []
    try_syntax = ''
    repo_urls = set()
    autoland_requests = AutolandRequest.objects.filter(
        review_request_id=parent.id).order_by('-autoland_id')

    # We would like to fetch the latest AutolandRequest for each
    # different repository.
    for land_request in autoland_requests:
        if land_request.repository_url in repo_urls:
            continue

        repo_urls.add(land_request.repository_url)
        latest_autoland_requests.append(land_request)
        try_syntax = try_syntax or land_request.extra_data.get('try_syntax', '')

    return {
        'review_request_details': review_request_details,
        'parent_details': parent_details,
        'children_details': children_details,
        'num_children': n_children,
        'current_child_num': current_child_num,
        'next_child': next_child,
        'prev_child': prev_child,
        'latest_autoland_requests': latest_autoland_requests,
        'user': user,
        'try_syntax': try_syntax,
    }

