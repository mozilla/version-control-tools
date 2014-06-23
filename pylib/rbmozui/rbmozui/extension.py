# rbmozui Extension for Review Board.

from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include
from reviewboard.extensions.base import Extension


class RBMozUI(Extension):
    metadata = {
        'Name': 'rbmozui',
        'Summary': 'UI tweaks to Review Board for Mozilla',
    }

    def initialize(self):
        # Your extension initialization is done here.
        pass
