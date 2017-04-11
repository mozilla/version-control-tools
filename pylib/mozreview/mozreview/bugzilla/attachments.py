from __future__ import unicode_literals

from mozreview.bugzilla.client import (
    BugzillaAttachmentUpdates,
)
from mozreview.errors import (
    BugzillaUserMapError,
)
from mozreview.extra_data import (
    REVIEW_FLAG_KEY,
)
from mozreview.models import (
    BugzillaUserMap,
    get_or_create_bugzilla_users,
)
from mozreview.rb_utils import (
    get_obj_url,
)
from mozreview.review_helpers import (
    gen_latest_reviews,
)


def update_bugzilla_attachments(bugzilla, bug_id, children_to_post,
                                children_to_obsolete):
    attachment_updates = BugzillaAttachmentUpdates(bugzilla, bug_id)

    for child in children_to_obsolete:
        attachment_updates.obsolete_review_attachments(get_obj_url(child))

    # We publish attachments for each commit/child to Bugzilla so that
    # reviewers can easily track their requests.

    # The review request exposes a list of usernames for reviewers. We need
    # to convert these to Bugzilla emails in order to make the request into
    # Bugzilla.
    #
    # It may seem like there is a data syncing problem here where usernames
    # may get out of sync with the reality from Bugzilla. Fortunately,
    # Review Board is smarter than that. Internally, the target_people list
    # is stored with foreign keys into the numeric primary key of the user
    # table. If the RB username changes, this won't impact target_people
    # nor the stored mapping to the numeric Bugzilla ID, which is
    # immutable.
    #
    # But we do have a potential data syncing problem with the stored email
    # address. Review Board's stored email address could be stale. So
    # instead of using it directly, we query Bugzilla and map the stored,
    # immutable numeric Bugzilla userid into an email address. This lookup
    # could be avoided if Bugzilla accepted a numeric userid in the
    # requestee parameter when modifying an attachment.
    user_email_cache = {}

    for review_request_draft, review_request in children_to_post:
        carry_forward = {}

        bum = BugzillaUserMap.objects.get(user=review_request_draft.submitter)
        submitter_email = bugzilla.get_user_from_userid(
            bum.bugzilla_user_id)['users'][0]['email']

        user_email_cache[bum.bugzilla_user_id] = submitter_email

        has_code_changes = review_request_draft.diffset is not None

        for u in review_request_draft.target_people.all():
            bum = BugzillaUserMap.objects.get(user=u)
            email = user_email_cache.get(bum.bugzilla_user_id)

            if email is None:
                user_data = bugzilla.get_user_from_userid(bum.bugzilla_user_id)

                # Since we're making the API call, we might as well ensure the
                # local database is up to date.
                users = get_or_create_bugzilla_users(user_data)
                # There is a chance the user requested a merge of accounts.
                # In such case bum will exist, but no user will be found
                # with userid = bum.bugzilla_user_id. MozReview should fail
                # gracefully
                if len(users) == 0:
                    raise BugzillaUserMapError(u.username)
                email = users[0].email
                user_email_cache[bum.bugzilla_user_id] = email

            carry_forward[email] = False

        for review in gen_latest_reviews(review_request):
            if has_code_changes:
                # The code has changed, we need to determine what needs to
                # happen to the flags.

                # Don't set carry_forward values for reviewers that are not in
                # the target_people list (eg. impromptu reviews).  This will
                # result in the attachment flag being cleared in Bugzilla.
                if review.user.email not in carry_forward:
                    continue

                # Carry forward just r+'s.  All other flags should be reset
                # to r?.
                review_flag = review.extra_data.get(REVIEW_FLAG_KEY)
                carry_forward[review.user.email] = review_flag == 'r+' or (
                    # Older reviews didn't set review_flag.
                    review_flag is None and review.ship_it)

            else:
                # This is a meta data only change, don't touch any existing
                # flags.
                carry_forward[review.user.email] = True

        flags = []
        attachment = attachment_updates.get_attachment(review_request)

        # Map of current r? flags, requestee -> flag object.
        #
        # If this review-request change is actually a reviewer delegating
        # reviews, that is, they are removing themselves and adding another
        # reviewer, we want to reuse the r? flag if possible.  In this case,
        # the person submitting the review-request update is not the
        # author, so they cannot create a new r? flag as though it were
        # coming from the author.  However, the reviewer ("requestee") of an
        # existing flag *can* be changed while preserving the flag creator.
        # Thus, we record them here and then match them up later.

        attachment_rq_flags = {}

        if attachment:
            # Update flags on an existing attachment.
            for f in attachment.get('flags', []):
                if f['name'] not in ['review', 'feedback']:
                    # We only care about review and feedback flags.
                    continue

                # When a new patch is pushed, we need to mimic what
                # happens to flags when a new attachment is created
                # in Bugzilla:
                # - carry forward r+'s
                # - clear r-'s
                # - clear feedback flags

                if f['name'] == 'feedback':
                    if has_code_changes:
                        # We always clear feedback flags when the patch
                        # is updated.
                        flags.append({'id': f['id'], 'status': 'X'})
                elif f['status'] == '+' or f['status'] == '-':
                    # A reviewer has left a review, either in Review Board or
                    # in Bugzilla.
                    if f['setter'] not in carry_forward:
                        # This flag was set manually in Bugzilla rather
                        # then through a review on Review Board. Always
                        # clear these flags.
                        flags.append({'id': f['id'], 'status': 'X'})
                    else:
                        # This flag was set through Review Board; see if
                        # we should carry it forward.
                        if not carry_forward[f['setter']]:
                            # We should not carry this r+/r- forward so
                            # re-request review.
                            flags.append({
                                'id': f['id'],
                                'name': 'review',
                                'status': '?',
                                'requestee': f['setter']
                            })
                        # else we leave the flag alone, carrying it forward.

                        # In either case, we've dealt with this reviewer, so
                        # remove it from the carry_forward dict.
                        carry_forward.pop(f['setter'])
                elif f['status'] == '?' and f['setter'] == submitter_email:
                    # Record this and sort out r? flags later.
                    attachment_rq_flags[f['requestee']] = f
                elif ('requestee' not in f or
                      f['requestee'] not in carry_forward):
                    # We clear review flags where the requestee is not
                    # a reviewer, or if there is some (possibly future) flag
                    # other than + or - that does not have a 'requestee' field.
                    flags.append({'id': f['id'], 'status': 'X'})
                elif f['requestee'] in carry_forward:
                    # We're already waiting for a review from this user
                    # so don't touch the flag.
                    carry_forward.pop(f['requestee'])

        # Add flags for new reviewers.
        #
        # We can't set a missing r+ (if it was manually removed) except in the
        # trivial (and useless) case that the setter and the requestee are the
        # same person.  We could set r? again, but in the event that the
        # reviewer is not accepting review requests, this will block
        # publishing, with no way for the author to fix it.  So we'll just
        # ignore manually removed r+s.
        #
        # This is sorted so behavior is deterministic (this mucks with test
        # output otherwise).

        # If there are existing r? flags and we want to re-request review for
        # that reviewer, don't send any update to the server so that we keep
        # the flag in place.

        for reviewer, keep in sorted(carry_forward.iteritems()):
            if not keep:
                if reviewer in attachment_rq_flags:
                    del(attachment_rq_flags[reviewer])
                    del(carry_forward[reviewer])

        # At this point, attachment_rq_flags contains r? flags that
        # are no longer needed.  Reuse them for any new r? so that the
        # creator is preserved.

        for reviewer, keep in sorted(carry_forward.iteritems()):
            if not keep:
                if attachment_rq_flags:
                    rr_flag = attachment_rq_flags.values()[0]
                    flags.append({
                        'id': rr_flag['id'],
                        'requestee': reviewer,
                        'status': '?',
                    })
                    del(attachment_rq_flags[rr_flag['requestee']])
                else:
                    flags.append({
                        'name': 'review',
                        'status': '?',
                        'requestee': reviewer,
                        'new': True
                    })

        # Clear any remaining r? flags.

        for reviewer, flag in attachment_rq_flags.iteritems():
            flags.append({'id': flag['id'], 'status': 'X'})

        attachment_updates.create_or_update_attachment(
            review_request, review_request_draft, flags)

    attachment_updates.do_updates()
