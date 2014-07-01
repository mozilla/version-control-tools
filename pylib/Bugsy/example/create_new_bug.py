import bugsy
bz = bugsy.Bugsy("someUser", "theirPassword", "https://bugzilla-dev.allizom.org/rest")
bug = bugsy.Bug()
bug.summary = "I love cheese"
bug.add_comment('I do love sausages')
bz.put(bug)
