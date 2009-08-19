"""qimportbz

Imports patches from bugzilla to your mercurial queue

Configuration section is entirely optional but potentially useful.

[qimportbz]
bugzilla = server-address (defaults to BUGZILLA environment varable or bugzilla.mozilla.org)
joinstr = string to join flags for commit messages (default is ' ')
patch_format = Formatting string used to create patch names automatically
msg_format = Formatting string used to create commit messages automatically

Formatting strings are the standard python format strings where a dictionary is used to supply the data. Any % characters must be escaped since Python's configuration parser will try to interpret them. There are 5 pieces of patch metadata available for use:

      "bugnum" : the bug number
      "id" : the patch id (internal bugzilla number)
      "title" : the bug title
      "desc" : the patch description
      "flags" : all the flags

The default values are:
patch_format = bug-%(bugnum)s
msg_format = Bug %(bugnum)s - "%(title)s" [%(flags)s]
"""
from commands import qimportbz

cmdtable = {
  "qimportbz" : (qimportbz,
                 [('r', 'dry-run', False, "Perform a dry run - the patch queue will remain unchanged"),
                  ('p', 'preview', False, "Preview commit message"),
                  ('n', 'patch-name', '', "Override patch name")],
                 "hg qimportbz [-v] [-r] [-p] [-n NAME] BUG#")
}
