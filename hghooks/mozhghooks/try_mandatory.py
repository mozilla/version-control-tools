#!/usr/bin/env python

chooserUrl = 'http://trychooser.pub.build.mozilla.org/'
infoUrl = 'https://wiki.mozilla.org/Build:TryChooser'


def printError(message):
    print "\n\n************************** ERROR ****************************"
    print message
    print "*************************************************************\n\n"


def hook(ui, repo, source=None, **kwargs):
    if source == 'strip':
        return 0

    # Block the push unless they use the try_syntax
    # 'try: ' is enough to activate try_parser and get the default set
    comment = repo.changectx('tip').description()
    info = { 'chooserUrl': chooserUrl, 'infoUrl': infoUrl }
    if "try: " not in comment:
        printError("""To push to try you must use try syntax in the push comment of the *last* change 
See %(chooserUrl)s to build your syntax
For assistance using the syntax, see %(infoUrl)s.
Thank you for helping to reduce CPU cyles by asking for exactly what you need.""" % info)
        return 1
    elif "-p none" in comment:
        printError("""Your try syntax contains '-p none', which would not trigger any jobs.
Please try try again. If you *intended* to push without triggering
any jobs, use -p any_invalid_syntax. For assistance with try server
syntax, see %(infoUrl)s.""" % info)
        return 1
    return 0
