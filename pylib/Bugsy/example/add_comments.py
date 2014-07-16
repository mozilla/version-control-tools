import bugsy
bz = bugsy.Bugsy("username", "password", "https://bugzilla-dev.allizom.org/rest")
bug = bugsy.Bug()
bug.summary = "I love cheese"
bug.add_comment('I do love sausages too')
bz.put(bug)

bug.add_comment('I do love eggs too')
