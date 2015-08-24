# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from collections import OrderedDict

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

import yaml


# Teach yaml how to format OrderedDict.
def ordered_dict_presenter(dumper, data):
    return dumper.represent_dict(data.items())
yaml.add_representer(OrderedDict, ordered_dict_presenter,
                     Dumper=yaml.SafeDumper)


def _serialize_text(s):
    lines = s.splitlines()
    if len(lines) > 1:
        return lines
    return s


def serialize_review_requests(rr):
    from rbtools.api.errors import APIError
    d = OrderedDict()
    d['id'] = rr.id
    d['status'] = rr.status
    d['public'] = rr.public
    d['bugs'] = list(rr.bugs_closed)
    d['commit'] = rr.commit_id
    d['submitter'] = rr.get_submitter().username
    d['summary'] = _serialize_text(rr.summary)
    d['description'] = _serialize_text(rr.description)
    d['target_people'] = [p.get().username for p in rr.target_people]
    d['extra_data'] = dict(rr.extra_data.iteritems())
    d['approved'] = rr.approved
    d['approval_failure'] = rr.approval_failure

    review_list = rr.get_reviews(review_request_id=rr.id)
    reviews = []
    for review in review_list:
        d['review_count'] = review_list.total_results

        rd = OrderedDict()
        rd['id'] = review.id
        rd['public'] = review.public
        rd['ship_it'] = review.ship_it
        if dict(review.extra_data.iteritems()):
            rd['extra_data'] = dict(review.extra_data.iteritems())
        if review.body_top:
            rd['body_top'] = _serialize_text(review.body_top)
            rd['body_top_text_type'] = review.body_top_text_type
        if review.body_bottom:
            rd['body_bottom'] = _serialize_text(review.body_bottom)
            rd['body_bottom_text_type'] = review.body_bottom_text_type

        rd['diff_comments'] = []

        diff_list = review.get_diff_comments()
        for comment in diff_list:
            rd['diff_count'] = diff_list.total_results

            cd = OrderedDict()

            user = comment.get_user()
            filediff = comment.get_filediff()
            # TODO handle interdiffs
            # interfilediff = comment.get_interfilediff()

            cd['id'] = comment.id
            cd['public'] = comment.public
            cd['user'] = user.username
            cd['issue_opened'] = comment.issue_opened
            if comment.issue_opened:
                cd['issue_status'] = comment.issue_status
            cd['first_line'] = comment.first_line
            cd['num_lines'] = comment.num_lines
            cd['text'] = _serialize_text(comment.text)
            cd['text_type'] = comment.text_type

            if dict(comment.extra_data.iteritems()):
                cd['extra_data'] = dict(comment.extra_data.iteritems())

            cd['diff_id'] = filediff.id
            cd['diff_dest_file'] = filediff.dest_file

            rd['diff_comments'].append(cd)

        reviews.append(rd)

    if reviews:
        d['reviews'] = reviews

    try:
        draft = rr.get_draft()
        ddraft = OrderedDict()
        d['draft'] = ddraft
        ddraft['bugs'] = list(draft.bugs_closed)
        ddraft['commit'] = draft.commit_id
        ddraft['summary'] = _serialize_text(draft.summary)
        ddraft['description'] = _serialize_text(draft.description)
        ddraft['target_people'] = [p.get().username for p in draft.target_people]
        ddraft['extra'] = dict(draft.extra_data.iteritems())

        ddraft['diffs'] = []
        for diff in draft.get_draft_diffs():
            diffd = OrderedDict()
            diffd['id'] = diff.id
            diffd['revision'] = diff.revision
            diffd['base_commit_id'] = diff.base_commit_id
            diffd['patch'] = diff.get_patch().data.splitlines()
            ddraft['diffs'].append(diffd)

    except APIError:
        pass

    return yaml.safe_dump(d, default_flow_style=False).rstrip()


def short_review_request_dict(rr):
    # Don't include last_updated since it's hard to test.
    d = OrderedDict()
    d['summary'] = _serialize_text(rr['summary'])

    for k in ('id', 'commit', 'submitter', 'issue_open_count', 'status'):
        if k in rr:
            d[k] = rr[k]

    d['reviewers'] = [x for x in rr['reviewers']]

    return d


@CommandProvider
class ReviewBoardCommands(object):
    def __init__(self, context):
        from vcttesting.mozreview import MozReview
        if 'MOZREVIEW_HOME' in os.environ:
            self.mr = MozReview(os.environ['MOZREVIEW_HOME'])
        else:
            self.mr = None

    def _get_client(self, username=None, password=None):
        from rbtools.api.client import RBClient
        from rbtools.api.transport.sync import SyncTransport

        class NoCacheTransport(SyncTransport):
            """API transport with disabled caching."""
            def enable_cache(self):
                pass

        # TODO consider moving this to __init__.
        if not self.mr:
            raise Exception('Could not find MozReview cluster instance')

        if username is None or password is None:
            username = os.environ.get('BUGZILLA_USERNAME')
            password = os.environ.get('BUGZILLA_PASSWORD')

        # RBClient is persisting login cookies from call to call
        # in $HOME/.rbtools-cookies. We want to be able to easily switch
        # between users, so we clear that cookie between calls to the
        # server and reauthenticate every time.
        try:
            os.remove(os.path.join(os.environ.get('HOME'), '.rbtools-cookies'))
        except Exception:
            pass

        return RBClient(self.mr.reviewboard_url, username=username,
                        password=password, transport_cls=NoCacheTransport)

    def _get_root(self, username=None, password=None):
        return self._get_client(username=username, password=password).get_root()

    def _get_rb(self, path=None):
        from vcttesting.reviewboard import MozReviewBoard

        if self.mr:
            return self.mr.get_reviewboard()
        elif 'BUGZILLA_HOME' in os.environ and path:
            return MozReviewBoard(None, os.environ['BUGZILLA_URL'],
                pulse_host=os.environ.get('PULSE_HOST'),
                pulse_port=os.environ.get('PULSE_PORT'))
        elif 'REVIEWBOARD_URL' in os.environ:
            return MozReviewBoard(None, None, os.environ['REVIEWBOARD_URL'])
        else:
            raise Exception('Do not know about Bugzilla URL. Cannot talk to '
                            'Review Board. Try running `mozreview start` and '
                            'setting MOZREVIEW_HOME.')

    @Command('dumpreview', category='reviewboard',
        description='Print a representation of a review request.')
    @CommandArgument('rrid', help='Review request id to dump')
    def dumpreview(self, rrid):
        root = self._get_root()
        r = root.get_review_request(review_request_id=rrid)
        print(serialize_review_requests(r))

    @Command('add-reviewer', category='reviewboard',
        description='Add a reviewer to a review request')
    @CommandArgument('rrid', help='Review request id to modify')
    @CommandArgument('--user', action='append',
        help='User from whom to ask for review')
    def add_reviewer(self, rrid, user):
        from rbtools.api.errors import APIError

        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)

        people = []
        draft = rr.get_or_create_draft()
        for p in draft.target_people:
            people.append(p.title)

        # Review Board doesn't call into the auth plugin when mapping target
        # people to RB users. So, we perform an API call here to ensure the
        # user is present.
        for u in user:
            if u not in people:
                people.append(u)
                root.get_users(q=u)

        people = ','.join(people)

        draft = rr.get_or_create_draft(target_people=people)
        print('%d people listed on review request' % len(draft.target_people))

    @Command('list-reviewers', category='reviewboard',
        description='List reviewers on a review request')
    @CommandArgument('rrid', help='Review request id for which to list reviewers')
    @CommandArgument('--draft', action='store_true',
            help='List reviewers on the current draft')
    def list_reviewers(self, rrid, draft):
        from rbtools.api.errors import APIError
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)

        people = []
        if draft:
            try:
                for p in rr.get_draft().target_people:
                    people.append(p.title)
            except APIError:
                pass
        else:
            for p in rr.target_people:
                people.append(p.title)

        print(', '.join(sorted(people)))

    @Command('remove-reviewer', category='reviewboard',
        description='Remove a reviewer from a review request')
    @CommandArgument('rrid', help='Review request id to modify')
    @CommandArgument('--user', action='append',
        help='User to remove from review')
    def remove_reviewer(self, rrid, user):
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)

        people = []
        for p in rr.target_people:
            username = p.get().username
            if username not in user:
                people.append(username)

        people = ','.join(people)

        draft = rr.get_or_create_draft(target_people=people)
        print('%d people listed on review request' % len(draft.target_people))

    @Command('publish', category='reviewboard',
        description='Publish a review request')
    @CommandArgument('rrid', help='Review request id to publish')
    def publish(self, rrid):
        from rbtools.api.errors import APIError
        root = self._get_root()
        r = root.get_review_request(review_request_id=rrid)

        try:
            response = r.get_draft().update(public=True)
            # TODO: Dump the response code?
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                e.rsp['err']['msg']))
            return 1

    @Command('get-users', category='reviewboard',
        description='Query the Review Board user list')
    @CommandArgument('q', help='Query string')
    def query_users(self, q=None):
        from rbtools.api.errors import APIError

        root = self._get_root()
        try:
            r = root.get_users(q=q, fullname=True)
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                e.rsp['err']['msg']))
            return 1

        users = []
        for u in r.rsp['users']:
            users.append(dict(
                id=u['id'],
                url=u['url'],
                username=u['username']))

        print(yaml.safe_dump(users, default_flow_style=False).rstrip())

    @Command('create-review', category='reviewboard',
        description='Create a new review on a review request')
    @CommandArgument('rrid', help='Review request to create the review on')
    @CommandArgument('--body-bottom',
            help='Review content below comments')
    @CommandArgument('--body-top',
            help='Review content above comments')
    @CommandArgument('--public', action='store_true',
            help='Whether to make this review public')
    @CommandArgument('--ship-it', action='store_true',
            help='Whether to mark the review "Ship It"')
    def create_review(self, rrid, body_bottom=None, body_top=None, public=False,
            ship_it=False):
        from rbtools.api.errors import APIError
        root = self._get_root()
        reviews = root.get_reviews(review_request_id=rrid)
        # rbtools will convert body_* to str() and insert "None" if we pass
        # an argument.
        args = {'public': public, 'ship_it': ship_it}
        if body_bottom:
            args['body_bottom'] = body_bottom
        if body_top:
            args['body_top'] = body_top

        try:
            r = reviews.create(**args)
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                                             e.rsp['err']['msg']))
            return 1

        print('created review %s' % r.rsp['review']['id'])

    @Command('publish-review', category='reviewboard',
        description='Publish a review')
    @CommandArgument('rrid', help='Review request review is attached to')
    @CommandArgument('rid', help='Review to publish')
    def publish_review(self, rrid, rid):
        from rbtools.api.errors import APIError
        root = self._get_root()
        review = root.get_review(review_request_id=rrid, review_id=rid)

        try:
            review.update(public=True)
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                                             e.rsp['err']['msg']))
            return 1

        print('published review %s' % review.id)

    @Command('create-review-reply', category='reviewboard',
        description='Create a reply to an existing review')
    @CommandArgument('rrid', help='Review request to create reply on')
    @CommandArgument('rid', help='Review to create reply on')
    @CommandArgument('--body-bottom',
        help='Reply content below the comments')
    @CommandArgument('--body-top',
        help='Reply content above the comments')
    @CommandArgument('--public', action='store_true',
        help='Whether to make this reply public')
    @CommandArgument('--text-type', default='plain',
        help='The format of the text')
    def create_review_reply(self, rrid, rid, body_bottom, body_top,
            public, text_type):
        root = self._get_root()
        replies = root.get_replies(review_request_id=rrid, review_id=rid)

        args = {'public': public, 'text_type': text_type}
        if body_bottom:
            args['body_bottom'] = body_bottom
        if body_top:
            args['body_top'] = body_top

        r = replies.create(**args)
        print('created review reply %s' % r.rsp['reply']['id'])

    @Command('create-diff-comment', category='reviewboard',
             description='Create a comment on a diff')
    @CommandArgument('rrid', help='Review request to create comment on')
    @CommandArgument('rid', help='Review to create comment on')
    @CommandArgument('filename', help='File to leave comment on')
    @CommandArgument('first_line', help='Line comment should apply to')
    @CommandArgument('text', help='Text constituting diff comment')
    @CommandArgument('--open-issue', action='store_true',
                     help='Whether to open an issue in this review')
    def create_diff_comment(self, rrid, rid, filename, first_line, text,
                            open_issue=False):
        root = self._get_root()

        diffs = root.get_diffs(review_request_id=rrid)
        diff = diffs[-1]
        files = diff.get_files()

        file_id = None
        for file_diff in files:
            if file_diff.source_file == filename:
                file_id = file_diff.id

        if not file_id:
            print('could not find file in diff: %s' % filename)
            return 1

        reviews = root.get_reviews(review_request_id=rrid)
        review = reviews.create()
        comments = review.get_diff_comments()
        comment = comments.create(filediff_id=file_id, first_line=first_line,
                                  num_lines=1, text=text,
                                  issue_opened=open_issue)
        print('created diff comment %s' % comment.id)

    @Command('update-issue-status', category='reviewboard',
             description='Update issue status on a diff comment.')
    @CommandArgument('rrid', help='Review request for the diff comment review')
    @CommandArgument('rid', help='Review for the diff comment')
    @CommandArgument('cid', help='Diff comment of issue to be updated')
    @CommandArgument('status', help='Desired issue status ("open", "dropped", '
                     'or "resolved")')
    def update_issue_status(self, rrid, rid, cid, status):
        root = self._get_root()

        review = root.get_review(review_request_id=rrid, review_id=rid)
        diff_comment = review.get_diff_comments().get_item(cid)
        diff_comment.update(issue_status=status)
        print('updated issue status on diff comment %s' % cid)

    @Command('closediscarded', category='reviewboard',
        description='Close a review request as discarded.')
    @CommandArgument('rrid', help='Request request to discard')
    def close_discarded(self, rrid):
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)
        rr.update(status='discarded')

    @Command('closesubmitted', category='reviewboard',
        description='Close a review request as submitted.')
    @CommandArgument('rrid', help='Request request to submit')
    def close_submitted(self, rrid):
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)
        rr.update(status='submitted')

    @Command('reopen', category='reviewboard',
        description='Reopen a closed review request')
    @CommandArgument('rrid', help='Review request to reopen')
    def reopen(self, rrid):
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)
        rr.update(status='pending')

    @Command('discard-review-request-draft', category='reviewboard',
        description='Discard (delete) a draft review request.')
    @CommandArgument('rrid', help='Review request whose draft to delete')
    def discard_draft(self, rrid):
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)
        draft = rr.get_draft()

        # Review Board sends an Content-Length 0 response with a JSON content
        # type. rbtools tries to parse this as JSON and raises a ValueError
        # in the process. This is a bug somewhere. Work around it by swallowing
        # the exception.
        try:
            draft.delete()
        except ValueError:
            pass
        print('Discarded draft for review request %s' % rrid)

    @Command('dump-user', category='reviewboard',
        description='Print a representation of a user.')
    @CommandArgument('username', help='Username whose info the print')
    def dump_user(self, username):
        root = self._get_root()
        u = root.get_user(username=username)

        o = {}
        for field in u.iterfields():
            o[field] = getattr(u, field)

        data = {}
        data[u.id] = o

        print(yaml.safe_dump(data, default_flow_style=False).rstrip())

    @Command('dump-user-ldap', category='reviewboard',
        description='Print the ldap username of a Review Board user.')
    @CommandArgument('username', help='Username whose info the print')
    def dump_user_ldap(self, username):
        root = self._get_root(username="mozreview", password="password")
        ext = root.get_extension(
            extension_name='mozreview.extension.MozReviewExtension')
        user = ext.get_ldap_associations().get_item(username).ldap_username

        if user:
            print('ldap username: %s' % user)
        else:
            print('no ldap username associated with %s' % username)

    @Command('associate-ldap-user', category='reviewboard',
        description='Associate an LDAP email address with a user.')
    @CommandArgument('username', help='Username to associate with ldap')
    @CommandArgument('email', help='LDAP email to associate')
    def associate_ldap_user(self, username, email):
        # We use the "mozreview" account which has the special permission
        # to read / associate ldap email addresses.
        root = self._get_root(username="mozreview", password="password")
        ext = root.get_extension(
            extension_name='mozreview.extension.MozReviewExtension')

        association = ext.get_ldap_associations().get_item(username)
        association.update(ldap_username=email)

        print('%s associated with %s' % (email, username))

    @Command('dump-autoland-requests', category='reviewboard',
             description='Dump the table of autoland requests.')
    def dump_autoland_requests(self):
        root = self._get_root()
        ext = root.get_extension(
            extension_name="mozreview.extension.MozReviewExtension")

        requests = ext.get_try_autoland_triggers()
        o = {}
        for request in requests:
            for field in request.iterfields():
                o[field] = getattr(request, field)
            print(yaml.safe_dump(o, default_flow_style=False).rstrip())

    @Command('dump-summary', category='reviewboard',
             description='Return parent and child review-request summary.')
    @CommandArgument('rrid', help='Parent review request id')
    def dump_summary(self, rrid):
        from rbtools.api.errors import APIError
        c = self._get_client()

        try:
            r = c.get_path('/extensions/mozreview.extension.MozReviewExtension'
                           '/summary/%s/' % rrid)
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                e.rsp['err']['msg']))
            return 1

        d = OrderedDict()
        d['parent'] = short_review_request_dict(r['parent'])
        d['children'] = [short_review_request_dict(x) for x in r['children']]

        print(yaml.safe_dump(d, default_flow_style=False).rstrip())

    @Command('dump-summaries-by-bug', category='reviewboard',
             description='Return parent and child review-request summaries '
                         'for a given bug.')
    @CommandArgument('bug', help='Bug id')
    def dump_summaries_by_bug(self, bug):
        from rbtools.api.errors import APIError
        c = self._get_client()

        try:
            r = c.get_path('/extensions/mozreview.extension.MozReviewExtension'
                           '/summary/', bug=bug)
        except APIError as e:
            print('API Error: %s: %s: %s' % (e.http_status, e.error_code,
                                             e.rsp['err']['msg']))
            return 1

        l = []

        for summary in r:
            d = OrderedDict()
            d['parent'] = short_review_request_dict(summary['parent'])
            d['children'] = [short_review_request_dict(x) for x in
                             summary['children']]
            l.append(d)

        print(yaml.safe_dump(l, default_flow_style=False).rstrip())

    @Command('make-admin', category='reviewboard',
        description='Make a user a superuser and staff user')
    @CommandArgument('email', help='Email address of user to modify')
    def make_admin(self, email):
        self._get_rb().make_admin(email)

    @Command('dump-account-profile', category='reviewboard',
         description='Dump the contents of the auth_user table')
    @CommandArgument('username', help='Username whose info the print')
    def dump_account_profile(self, username):
        fields = self._get_rb().get_profile_data(username)
        for k, v in sorted(fields.items()):
            print('%s: %s' % (k, v))

    @Command('convert-draft-rids-to-str', category='reviewboard',
         description='Convert any review ids stored in extra data to strings')
    @CommandArgument('rrid', help='Review request id convert')
    def convert_draft_rids_to_str(self, rrid):
        from rbtools.api.errors import APIError
        import json
        root = self._get_root()
        rr = root.get_review_request(review_request_id=rrid)
        try:
            draft = rr.get_draft()
            d = dict(draft.extra_data.iteritems())

            extra_data = {}
            fields = ['p2rb.commits', 'p2rb.discard_on_publish_rids',
                      'p2rb.unpublished_rids']
            for field in fields:
                if field not in d:
                    continue
                try:
                    value = [[x[0], str(x[1])] for x in json.loads(d[field])]
                except TypeError:
                    value = [str(x) for x in json.loads(d[field])]
                extra_data['extra_data.' + field] = json.dumps(value)
            rr.get_or_create_draft(**extra_data)
        except APIError:
            pass

    @Command('add-repository', category='reviewboard',
             description='Add a repository to the server.')
    @CommandArgument('name', help='Name of repository')
    @CommandArgument('url', help='URL of repository')
    @CommandArgument('--bug-tracker',
                     default='https://bugzilla.mozilla.org/',
                     help='URL for bug tracker')
    def add_repository(self, name, url, bug_tracker=None):
        rb = self._get_rb()
        rid = rb.add_repository(name, url, bugzilla_url=bug_tracker,
                                username=os.environ['BUGZILLA_USERNAME'],
                                password=os.environ['BUGZILLA_PASSWORD'])
        print('Created repository %s' % rid)
