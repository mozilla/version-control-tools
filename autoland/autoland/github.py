import github3
import json
import os

class MockGithub3(object):
    """ This class mocks out the github3 stuff we use to allow us to test
        without access to github. """

    def pull_request(self, user, repo, pullrequest):
        class PullRequest(object):
            title = 'A pullrequest'
            body = 'A body'

            def commits(self):
                class Commit(object):
                    sha = '05830c796e2b0e9049c9e9cd463d987f4aedf4a35'
                    def patch(self):
                        return """# HG changeset patch
# User Cthulhu <cthulhu@mozilla.com>
# Date 1428426710 14400
#      Tue Apr 07 13:11:50 2015 -0400
# Node ID 5830c796e2b0e9049c9e9cd463d987f4aedf4a35
# Parent  0000000000000000000000000000000000000000
bug 1 - did stuff

diff --git a/hello b/hello
new file mode 100644
--- /dev/null
+++ b/hello
@@ -0,0 +1,1 @@
+hello, world!"""
                return [Commit()]
        return PullRequest()

    def issue(self, user, repo, issue):
        class Issue(object):
           def create_comment(self, comment):
                return True
        return Issue()


def connect():
    with open('config.json') as f:
        config = json.load(f)
        credentials = config['github']
        testing = config.get('testing', False)

    if testing:
        return MockGithub3()

    return github3.login(credentials['user'], password=credentials['passwd'])


def retrieve_issue(gh, user, repo, issue):
    title = None
    description = None
    commits = []

    i = gh.issue(user, repo, issue)

    if i:
        return i.title, i.body

    return None, None
 

def retrieve_commits(gh, user, repo, pullrequest, path):
    commits = []

    pr = gh.pull_request(user, repo, pullrequest)

    if pr:
        for commit in pr.commits():
            with open(os.path.join(path, commit.sha), 'w') as f:
                f.write(commit.patch())
            commits.append(commit.sha)

    return commits


def add_issue_comment(gh, user, repo, pullrequest, message):
    # TODO: presumably this raises something if it fails
    issue = gh.issue(user, repo, pullrequest)
    if issue:
        issue.create_comment(message)
        return True


def url_for_pullrequest(user, repo, pullrequest):
    return 'https://github.com/%s/%s/pull/%s' % (user, repo, pullrequest)
