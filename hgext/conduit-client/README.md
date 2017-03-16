# conduit-client hg extension

Enable the extension by adding a line to your .hgrc configuration, e.g:
`conduitext = ~/version-control-tools/hgext/conduit-client/client.py`


Doing so will enable the `hg conduitstage` command. Running this
command on the client will trigger the corresponding server extension
enabled on the remote repo to stage the commits in the conduit commit
index, which may later be used for requesting review.


This command doesn't push the actual commits, yet. In general, this
extension isn't usable at the time of this commit, because the server
extension and the whole conduit ecosystem is still in development.


## Examples
```
hg conduitstage -r 105::110 https://staging-hg.mozilla.org/project
```
This would request a review for all non-public, non-empty commits
between and including local id 105 to 110.

```
hg conduitstage -r . https://staging-hg.mozilla.org/project
```
This would request a review for only the current commit, no ancestors.
A bookmark, local id, or full commit id can be used in place of '.'


```
hg conduitstage --drafts -r 123 https://staging-hg.mozilla.org/project
```
This would request a review for commit 123 and all of
it's non-public ancestors (perhaps commits 121, 122, and 123).
If -r is not specified, will use the current commit as the start.


## Testing
You will need to have version-control-tools setup for testing already.
I.e. all the dependencies in vct/test-requirements.txt should be installed.
(This and more can be done with `./create-test-environment`).


This extension has only been tested with Mercurial 4.0, so you may have to
switch your system version to that.


### Manual Testing:
Create a hg repo as you normally would and create commits how you see fit.
Run `hg conduitstage revset http://localhost:77777` to see which
commits would ultimately be published. That URL is a magic string to bypass
an actual request since there is no server to talk to yet.


### Automated Tests:
Ensure that you were able to run the vct mercurial tests already.
`cd vct && python run-tests hgext/conduit-client`
