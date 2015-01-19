from django.conf.urls import patterns

from mozreview.extension import MozReviewExtension
from mozreview.forms import MozReviewSettingsForm


urlpatterns = patterns(
    '',
    (r'^$', 'reviewboard.extensions.views.configure_extension',
     {
         'ext_class': MozReviewExtension,
         'form_class': MozReviewSettingsForm,
     }),
)
