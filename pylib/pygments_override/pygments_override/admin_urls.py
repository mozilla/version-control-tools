from django.conf.urls import patterns, url

from pygments_override.extension import PygmentsOverride
from pygments_override.forms import PygmentsOverrideSettingsForm

urlpatterns = patterns('', url(
    r'^$', 'reviewboard.extensions.views.configure_extension', {
        'ext_class': PygmentsOverride,
        'form_class': PygmentsOverrideSettingsForm
    }))
