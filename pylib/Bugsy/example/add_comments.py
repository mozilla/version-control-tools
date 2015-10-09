import bugsy
bz = bugsy.Bugsy("username", "password", "https://bugzilla-dev.allizom.org/rest")

# Create a new bug with a comment 0 set.
bug = bugsy.Bug()
bug.summary = "I love cheese"
bug.add_comment('I do love sausages too')
bz.put(bug)

# Add another comment to that bug.
bug.add_comment('I do love eggs too')

# Add a comment to an existing bug for whom we don't
# have a bug object (and don't wish to fetch it).
bug = bz.get(123456)
bug.add_comment("I love cheese")
