from __future__ import unicode_literals

from django.conf.urls import patterns

from rbmozui.extension import RBMozUI
from rbmozui.forms import TryAutolandSettingsForm


urlpatterns = patterns(
    '',
    (r'^$', 'reviewboard.extensions.views.configure_extension',
     {
         'ext_class': RBMozUI,
         'form_class': TryAutolandSettingsForm,
     }),
)
