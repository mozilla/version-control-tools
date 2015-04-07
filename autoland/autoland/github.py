import github3
import json
import os

def connect():
    with open('config.json') as f:
        credentials = json.load(f)['github']

    return github3.login(credentials['user'], password=credentials['passwd'])


def retrieve_commits(gh, user, repo, pullrequest, path):
    commits = []

    # TODO: presumably this raises something if it fails
    pr = gh.pull_request(user, repo, pullrequest)

    if pr:
        for commit in pr.commits():
            with open(os.path.join(path, commit.sha), 'w') as f:
                f.write(commit.patch())
            commits.append(commit.sha)

    return commits


def add_pullrequest_comment(gh, user, repo, pullrequest, message):
    # TODO: presumably this raises something if it fails
    issue = gh.issue(user, repo, pullrequest)
    if issue:
        issue.create_comment(message)
        return True
