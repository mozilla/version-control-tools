# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board client extension."""

def extsetup(ui):
    ui.warn('the MozReview service has been disabled; '
            'stop loading the reviewboard/mozreview extension from your hgrc '
            'files to make this warning go away\n')
