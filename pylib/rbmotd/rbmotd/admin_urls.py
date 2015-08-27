from django.conf.urls import patterns

from rbmotd.extension import MotdExtension
from rbmotd.forms import MotdSettingsForm


urlpatterns = patterns(
    '',

    (r'^$', 'reviewboard.extensions.views.configure_extension',
     {
         'ext_class': MotdExtension,
         'form_class': MotdSettingsForm,
     }),
)
