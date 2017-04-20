  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ export BETAMAX_CASSETTE=linearize-github-pull-request-messages

  $ git init -q grepo
  $ cd grepo
  $ echo 0 > foo
  $ git add foo
  $ git commit -q -m initial

Reference a pull request to trigger GitHub API fetching.
The origin account is purposefully incorrect to prove that API data is used.

  $ echo 1 > foo
  $ cat > message << EOF
  > Auto merge of #16549 - wrong_account:wrong_repo, r=emilio
  > 
  > First line after summary line.
  > 
  > https://bugzilla.mozilla.org/show_bug.cgi?id=1357973
  > EOF

  $ git commit -q --all -F message

  $ linearize-git --normalize-github-merge-message --source-repo https://github.com/servo/servo --github-token dummy . heads/master
  linearizing 2 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to d477d7c32c063427971dff0fc479b44482c6988d)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 d477d7c32c063427971dff0fc479b44482c6988d Auto merge of #16549 - wrong_account:wrong_repo, r=emilio
  2 commits from heads/master converted; original: d477d7c32c063427971dff0fc479b44482c6988d; rewritten: 64c20d6f09fb0c86c8472f6982616937166920e7

  $ git log refs/convert/dest/heads/master
  commit 64c20d6f09fb0c86c8472f6982616937166920e7
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #16549 - store simple selectors and combinators inline (from bholley:inline_selectors); r=emilio
      
      First line after summary line.
      
      https://bugzilla.mozilla.org/show_bug.cgi?id=1357973
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial

GitHub API responses should be cached

  $ cat github-cache/user-bholley.json
  {
    "avatar_url": "https://avatars2.githubusercontent.com/u/377435?v=3",
    "bio": null,
    "blog": "http://bholley.net",
    "company": "Mozilla",
    "created_at": "2010-08-27T00:17:16Z",
    "email": "bobbyholley@gmail.com",
    "events_url": "https://api.github.com/users/bholley/events{/privacy}",
    "followers": 40,
    "followers_url": "https://api.github.com/users/bholley/followers",
    "following": 0,
    "following_url": "https://api.github.com/users/bholley/following{/other_user}",
    "gists_url": "https://api.github.com/users/bholley/gists{/gist_id}",
    "gravatar_id": "",
    "hireable": null,
    "html_url": "https://github.com/bholley",
    "id": 377435,
    "location": null,
    "login": "bholley",
    "name": "Bobby Holley",
    "organizations_url": "https://api.github.com/users/bholley/orgs",
    "public_gists": 1,
    "public_repos": 22,
    "received_events_url": "https://api.github.com/users/bholley/received_events",
    "repos_url": "https://api.github.com/users/bholley/repos",
    "site_admin": false,
    "starred_url": "https://api.github.com/users/bholley/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/bholley/subscriptions",
    "type": "User",
    "updated_at": "2017-04-18T17:26:07Z",
    "url": "https://api.github.com/users/bholley"
  } (no-eol)

  $ cat github-cache/pr-16549.json
  {
    "_links": {
      "comments": {
        "href": "https://api.github.com/repos/servo/servo/issues/16549/comments"
      },
      "commits": {
        "href": "https://api.github.com/repos/servo/servo/pulls/16549/commits"
      },
      "html": {
        "href": "https://github.com/servo/servo/pull/16549"
      },
      "issue": {
        "href": "https://api.github.com/repos/servo/servo/issues/16549"
      },
      "review_comment": {
        "href": "https://api.github.com/repos/servo/servo/pulls/comments{/number}"
      },
      "review_comments": {
        "href": "https://api.github.com/repos/servo/servo/pulls/16549/comments"
      },
      "self": {
        "href": "https://api.github.com/repos/servo/servo/pulls/16549"
      },
      "statuses": {
        "href": "https://api.github.com/repos/servo/servo/statuses/fe97033aa877f85e1ad2438245861a4425977e9b"
      }
    },
    "additions": 863,
    "assignee": {
      "avatar_url": "https://avatars2.githubusercontent.com/u/1323194?v=3",
      "events_url": "https://api.github.com/users/emilio/events{/privacy}",
      "followers_url": "https://api.github.com/users/emilio/followers",
      "following_url": "https://api.github.com/users/emilio/following{/other_user}",
      "gists_url": "https://api.github.com/users/emilio/gists{/gist_id}",
      "gravatar_id": "",
      "html_url": "https://github.com/emilio",
      "id": 1323194,
      "login": "emilio",
      "organizations_url": "https://api.github.com/users/emilio/orgs",
      "received_events_url": "https://api.github.com/users/emilio/received_events",
      "repos_url": "https://api.github.com/users/emilio/repos",
      "site_admin": false,
      "starred_url": "https://api.github.com/users/emilio/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/emilio/subscriptions",
      "type": "User",
      "url": "https://api.github.com/users/emilio"
    },
    "assignees": [
      {
        "avatar_url": "https://avatars2.githubusercontent.com/u/1323194?v=3",
        "events_url": "https://api.github.com/users/emilio/events{/privacy}",
        "followers_url": "https://api.github.com/users/emilio/followers",
        "following_url": "https://api.github.com/users/emilio/following{/other_user}",
        "gists_url": "https://api.github.com/users/emilio/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/emilio",
        "id": 1323194,
        "login": "emilio",
        "organizations_url": "https://api.github.com/users/emilio/orgs",
        "received_events_url": "https://api.github.com/users/emilio/received_events",
        "repos_url": "https://api.github.com/users/emilio/repos",
        "site_admin": false,
        "starred_url": "https://api.github.com/users/emilio/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/emilio/subscriptions",
        "type": "User",
        "url": "https://api.github.com/users/emilio"
      }
    ],
    "base": {
      "label": "servo:master",
      "ref": "master",
      "repo": {
        "archive_url": "https://api.github.com/repos/servo/servo/{archive_format}{/ref}",
        "assignees_url": "https://api.github.com/repos/servo/servo/assignees{/user}",
        "blobs_url": "https://api.github.com/repos/servo/servo/git/blobs{/sha}",
        "branches_url": "https://api.github.com/repos/servo/servo/branches{/branch}",
        "clone_url": "https://github.com/servo/servo.git",
        "collaborators_url": "https://api.github.com/repos/servo/servo/collaborators{/collaborator}",
        "comments_url": "https://api.github.com/repos/servo/servo/comments{/number}",
        "commits_url": "https://api.github.com/repos/servo/servo/commits{/sha}",
        "compare_url": "https://api.github.com/repos/servo/servo/compare/{base}...{head}",
        "contents_url": "https://api.github.com/repos/servo/servo/contents/{+path}",
        "contributors_url": "https://api.github.com/repos/servo/servo/contributors",
        "created_at": "2012-02-08T19:07:25Z",
        "default_branch": "master",
        "deployments_url": "https://api.github.com/repos/servo/servo/deployments",
        "description": "The Servo Browser Engine",
        "downloads_url": "https://api.github.com/repos/servo/servo/downloads",
        "events_url": "https://api.github.com/repos/servo/servo/events",
        "fork": false,
        "forks": 1586,
        "forks_count": 1586,
        "forks_url": "https://api.github.com/repos/servo/servo/forks",
        "full_name": "servo/servo",
        "git_commits_url": "https://api.github.com/repos/servo/servo/git/commits{/sha}",
        "git_refs_url": "https://api.github.com/repos/servo/servo/git/refs{/sha}",
        "git_tags_url": "https://api.github.com/repos/servo/servo/git/tags{/sha}",
        "git_url": "git://github.com/servo/servo.git",
        "has_downloads": true,
        "has_issues": true,
        "has_pages": false,
        "has_projects": false,
        "has_wiki": true,
        "homepage": "https://servo.org/",
        "hooks_url": "https://api.github.com/repos/servo/servo/hooks",
        "html_url": "https://github.com/servo/servo",
        "id": 3390243,
        "issue_comment_url": "https://api.github.com/repos/servo/servo/issues/comments{/number}",
        "issue_events_url": "https://api.github.com/repos/servo/servo/issues/events{/number}",
        "issues_url": "https://api.github.com/repos/servo/servo/issues{/number}",
        "keys_url": "https://api.github.com/repos/servo/servo/keys{/key_id}",
        "labels_url": "https://api.github.com/repos/servo/servo/labels{/name}",
        "language": null,
        "languages_url": "https://api.github.com/repos/servo/servo/languages",
        "merges_url": "https://api.github.com/repos/servo/servo/merges",
        "milestones_url": "https://api.github.com/repos/servo/servo/milestones{/number}",
        "mirror_url": null,
        "name": "servo",
        "notifications_url": "https://api.github.com/repos/servo/servo/notifications{?since,all,participating}",
        "open_issues": 2162,
        "open_issues_count": 2162,
        "owner": {
          "avatar_url": "https://avatars2.githubusercontent.com/u/2566135?v=3",
          "events_url": "https://api.github.com/users/servo/events{/privacy}",
          "followers_url": "https://api.github.com/users/servo/followers",
          "following_url": "https://api.github.com/users/servo/following{/other_user}",
          "gists_url": "https://api.github.com/users/servo/gists{/gist_id}",
          "gravatar_id": "",
          "html_url": "https://github.com/servo",
          "id": 2566135,
          "login": "servo",
          "organizations_url": "https://api.github.com/users/servo/orgs",
          "received_events_url": "https://api.github.com/users/servo/received_events",
          "repos_url": "https://api.github.com/users/servo/repos",
          "site_admin": false,
          "starred_url": "https://api.github.com/users/servo/starred{/owner}{/repo}",
          "subscriptions_url": "https://api.github.com/users/servo/subscriptions",
          "type": "Organization",
          "url": "https://api.github.com/users/servo"
        },
        "private": false,
        "pulls_url": "https://api.github.com/repos/servo/servo/pulls{/number}",
        "pushed_at": "2017-04-21T00:20:30Z",
        "releases_url": "https://api.github.com/repos/servo/servo/releases{/id}",
        "size": 326890,
        "ssh_url": "git@github.com:servo/servo.git",
        "stargazers_count": 9259,
        "stargazers_url": "https://api.github.com/repos/servo/servo/stargazers",
        "statuses_url": "https://api.github.com/repos/servo/servo/statuses/{sha}",
        "subscribers_url": "https://api.github.com/repos/servo/servo/subscribers",
        "subscription_url": "https://api.github.com/repos/servo/servo/subscription",
        "svn_url": "https://github.com/servo/servo",
        "tags_url": "https://api.github.com/repos/servo/servo/tags",
        "teams_url": "https://api.github.com/repos/servo/servo/teams",
        "trees_url": "https://api.github.com/repos/servo/servo/git/trees{/sha}",
        "updated_at": "2017-04-20T20:48:47Z",
        "url": "https://api.github.com/repos/servo/servo",
        "watchers": 9259,
        "watchers_count": 9259
      },
      "sha": "93fa0ae1e3bcfe9e70a6fea91d137f20d8b5f790",
      "user": {
        "avatar_url": "https://avatars2.githubusercontent.com/u/2566135?v=3",
        "events_url": "https://api.github.com/users/servo/events{/privacy}",
        "followers_url": "https://api.github.com/users/servo/followers",
        "following_url": "https://api.github.com/users/servo/following{/other_user}",
        "gists_url": "https://api.github.com/users/servo/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/servo",
        "id": 2566135,
        "login": "servo",
        "organizations_url": "https://api.github.com/users/servo/orgs",
        "received_events_url": "https://api.github.com/users/servo/received_events",
        "repos_url": "https://api.github.com/users/servo/repos",
        "site_admin": false,
        "starred_url": "https://api.github.com/users/servo/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/servo/subscriptions",
        "type": "Organization",
        "url": "https://api.github.com/users/servo"
      }
    },
    "body": "https://bugzilla.mozilla.org/show_bug.cgi?id=1357973\n\n<!-- Reviewable:start -->\n---\nThis change is\u2002[<img src=\"https://reviewable.io/review_button.svg\" height=\"34\" align=\"absmiddle\" alt=\"Reviewable\"/>](https://reviewable.io/reviews/servo/servo/16549)\n<!-- Reviewable:end -->\n",
    "body_html": "<p><a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1357973\">https://bugzilla.mozilla.org/show_bug.cgi?id=1357973</a></p>\n\n<hr>\n<p>This change is\u2002<a href=\"https://reviewable.io/reviews/servo/servo/16549\"><img src=\"https://camo.githubusercontent.com/0210135a140627a19496177795afadacb8502c1f/68747470733a2f2f72657669657761626c652e696f2f7265766965775f627574746f6e2e737667\" height=\"34\" align=\"absmiddle\" alt=\"Reviewable\" data-canonical-src=\"https://reviewable.io/review_button.svg\" style=\"max-width:100%;\"></a></p>\n",
    "body_text": "https://bugzilla.mozilla.org/show_bug.cgi?id=1357973\n\n\nThis change is\u2002",
    "changed_files": 11,
    "closed_at": "2017-04-20T22:42:23Z",
    "comments": 10,
    "comments_url": "https://api.github.com/repos/servo/servo/issues/16549/comments",
    "commits": 4,
    "commits_url": "https://api.github.com/repos/servo/servo/pulls/16549/commits",
    "created_at": "2017-04-20T21:01:53Z",
    "deletions": 483,
    "diff_url": "https://github.com/servo/servo/pull/16549.diff",
    "head": {
      "label": "bholley:inline_selectors",
      "ref": "inline_selectors",
      "repo": {
        "archive_url": "https://api.github.com/repos/bholley/servo/{archive_format}{/ref}",
        "assignees_url": "https://api.github.com/repos/bholley/servo/assignees{/user}",
        "blobs_url": "https://api.github.com/repos/bholley/servo/git/blobs{/sha}",
        "branches_url": "https://api.github.com/repos/bholley/servo/branches{/branch}",
        "clone_url": "https://github.com/bholley/servo.git",
        "collaborators_url": "https://api.github.com/repos/bholley/servo/collaborators{/collaborator}",
        "comments_url": "https://api.github.com/repos/bholley/servo/comments{/number}",
        "commits_url": "https://api.github.com/repos/bholley/servo/commits{/sha}",
        "compare_url": "https://api.github.com/repos/bholley/servo/compare/{base}...{head}",
        "contents_url": "https://api.github.com/repos/bholley/servo/contents/{+path}",
        "contributors_url": "https://api.github.com/repos/bholley/servo/contributors",
        "created_at": "2013-10-08T17:55:47Z",
        "default_branch": "master",
        "deployments_url": "https://api.github.com/repos/bholley/servo/deployments",
        "description": "The Servo Browser Engine",
        "downloads_url": "https://api.github.com/repos/bholley/servo/downloads",
        "events_url": "https://api.github.com/repos/bholley/servo/events",
        "fork": true,
        "forks": 0,
        "forks_count": 0,
        "forks_url": "https://api.github.com/repos/bholley/servo/forks",
        "full_name": "bholley/servo",
        "git_commits_url": "https://api.github.com/repos/bholley/servo/git/commits{/sha}",
        "git_refs_url": "https://api.github.com/repos/bholley/servo/git/refs{/sha}",
        "git_tags_url": "https://api.github.com/repos/bholley/servo/git/tags{/sha}",
        "git_url": "git://github.com/bholley/servo.git",
        "has_downloads": true,
        "has_issues": false,
        "has_pages": false,
        "has_projects": true,
        "has_wiki": true,
        "homepage": "",
        "hooks_url": "https://api.github.com/repos/bholley/servo/hooks",
        "html_url": "https://github.com/bholley/servo",
        "id": 13421111,
        "issue_comment_url": "https://api.github.com/repos/bholley/servo/issues/comments{/number}",
        "issue_events_url": "https://api.github.com/repos/bholley/servo/issues/events{/number}",
        "issues_url": "https://api.github.com/repos/bholley/servo/issues{/number}",
        "keys_url": "https://api.github.com/repos/bholley/servo/keys{/key_id}",
        "labels_url": "https://api.github.com/repos/bholley/servo/labels{/name}",
        "language": null,
        "languages_url": "https://api.github.com/repos/bholley/servo/languages",
        "merges_url": "https://api.github.com/repos/bholley/servo/merges",
        "milestones_url": "https://api.github.com/repos/bholley/servo/milestones{/number}",
        "mirror_url": null,
        "name": "servo",
        "notifications_url": "https://api.github.com/repos/bholley/servo/notifications{?since,all,participating}",
        "open_issues": 0,
        "open_issues_count": 0,
        "owner": {
          "avatar_url": "https://avatars2.githubusercontent.com/u/377435?v=3",
          "events_url": "https://api.github.com/users/bholley/events{/privacy}",
          "followers_url": "https://api.github.com/users/bholley/followers",
          "following_url": "https://api.github.com/users/bholley/following{/other_user}",
          "gists_url": "https://api.github.com/users/bholley/gists{/gist_id}",
          "gravatar_id": "",
          "html_url": "https://github.com/bholley",
          "id": 377435,
          "login": "bholley",
          "organizations_url": "https://api.github.com/users/bholley/orgs",
          "received_events_url": "https://api.github.com/users/bholley/received_events",
          "repos_url": "https://api.github.com/users/bholley/repos",
          "site_admin": false,
          "starred_url": "https://api.github.com/users/bholley/starred{/owner}{/repo}",
          "subscriptions_url": "https://api.github.com/users/bholley/subscriptions",
          "type": "User",
          "url": "https://api.github.com/users/bholley"
        },
        "private": false,
        "pulls_url": "https://api.github.com/repos/bholley/servo/pulls{/number}",
        "pushed_at": "2017-04-20T22:05:06Z",
        "releases_url": "https://api.github.com/repos/bholley/servo/releases{/id}",
        "size": 249850,
        "ssh_url": "git@github.com:bholley/servo.git",
        "stargazers_count": 0,
        "stargazers_url": "https://api.github.com/repos/bholley/servo/stargazers",
        "statuses_url": "https://api.github.com/repos/bholley/servo/statuses/{sha}",
        "subscribers_url": "https://api.github.com/repos/bholley/servo/subscribers",
        "subscription_url": "https://api.github.com/repos/bholley/servo/subscription",
        "svn_url": "https://github.com/bholley/servo",
        "tags_url": "https://api.github.com/repos/bholley/servo/tags",
        "teams_url": "https://api.github.com/repos/bholley/servo/teams",
        "trees_url": "https://api.github.com/repos/bholley/servo/git/trees{/sha}",
        "updated_at": "2015-10-09T02:34:11Z",
        "url": "https://api.github.com/repos/bholley/servo",
        "watchers": 0,
        "watchers_count": 0
      },
      "sha": "fe97033aa877f85e1ad2438245861a4425977e9b",
      "user": {
        "avatar_url": "https://avatars2.githubusercontent.com/u/377435?v=3",
        "events_url": "https://api.github.com/users/bholley/events{/privacy}",
        "followers_url": "https://api.github.com/users/bholley/followers",
        "following_url": "https://api.github.com/users/bholley/following{/other_user}",
        "gists_url": "https://api.github.com/users/bholley/gists{/gist_id}",
        "gravatar_id": "",
        "html_url": "https://github.com/bholley",
        "id": 377435,
        "login": "bholley",
        "organizations_url": "https://api.github.com/users/bholley/orgs",
        "received_events_url": "https://api.github.com/users/bholley/received_events",
        "repos_url": "https://api.github.com/users/bholley/repos",
        "site_admin": false,
        "starred_url": "https://api.github.com/users/bholley/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/bholley/subscriptions",
        "type": "User",
        "url": "https://api.github.com/users/bholley"
      }
    },
    "html_url": "https://github.com/servo/servo/pull/16549",
    "id": 116863705,
    "issue_url": "https://api.github.com/repos/servo/servo/issues/16549",
    "locked": false,
    "maintainer_can_modify": false,
    "merge_commit_sha": "fe97033aa877f85e1ad2438245861a4425977e9b",
    "mergeable": null,
    "mergeable_state": "unknown",
    "merged": true,
    "merged_at": "2017-04-20T22:42:23Z",
    "merged_by": {
      "avatar_url": "https://avatars2.githubusercontent.com/u/4368172?v=3",
      "events_url": "https://api.github.com/users/bors-servo/events{/privacy}",
      "followers_url": "https://api.github.com/users/bors-servo/followers",
      "following_url": "https://api.github.com/users/bors-servo/following{/other_user}",
      "gists_url": "https://api.github.com/users/bors-servo/gists{/gist_id}",
      "gravatar_id": "",
      "html_url": "https://github.com/bors-servo",
      "id": 4368172,
      "login": "bors-servo",
      "organizations_url": "https://api.github.com/users/bors-servo/orgs",
      "received_events_url": "https://api.github.com/users/bors-servo/received_events",
      "repos_url": "https://api.github.com/users/bors-servo/repos",
      "site_admin": false,
      "starred_url": "https://api.github.com/users/bors-servo/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/bors-servo/subscriptions",
      "type": "User",
      "url": "https://api.github.com/users/bors-servo"
    },
    "milestone": null,
    "number": 16549,
    "patch_url": "https://github.com/servo/servo/pull/16549.patch",
    "rebaseable": null,
    "review_comment_url": "https://api.github.com/repos/servo/servo/pulls/comments{/number}",
    "review_comments": 0,
    "review_comments_url": "https://api.github.com/repos/servo/servo/pulls/16549/comments",
    "state": "closed",
    "statuses_url": "https://api.github.com/repos/servo/servo/statuses/fe97033aa877f85e1ad2438245861a4425977e9b",
    "title": "store simple selectors and combinators inline",
    "updated_at": "2017-04-20T22:42:24Z",
    "url": "https://api.github.com/repos/servo/servo/pulls/16549",
    "user": {
      "avatar_url": "https://avatars2.githubusercontent.com/u/377435?v=3",
      "events_url": "https://api.github.com/users/bholley/events{/privacy}",
      "followers_url": "https://api.github.com/users/bholley/followers",
      "following_url": "https://api.github.com/users/bholley/following{/other_user}",
      "gists_url": "https://api.github.com/users/bholley/gists{/gist_id}",
      "gravatar_id": "",
      "html_url": "https://github.com/bholley",
      "id": 377435,
      "login": "bholley",
      "organizations_url": "https://api.github.com/users/bholley/orgs",
      "received_events_url": "https://api.github.com/users/bholley/received_events",
      "repos_url": "https://api.github.com/users/bholley/repos",
      "site_admin": false,
      "starred_url": "https://api.github.com/users/bholley/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/bholley/subscriptions",
      "type": "User",
      "url": "https://api.github.com/users/bholley"
    }
  } (no-eol)

