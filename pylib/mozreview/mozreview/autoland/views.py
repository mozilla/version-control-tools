from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.template.loader import Context, get_template
from mozreview.autoland.resources import import_pullrequest_trigger_resource
from reviewboard.extensions.base import get_extension_manager


@login_required
def import_pullrequest(request, user, repo, pullrequest):
    ext = get_extension_manager().get_enabled_extension(
        'mozreview.extension.MozReviewExtension')
    enabled = ext.get_settings('autoland_import_pullrequest_ui_enabled', False)

    if not enabled:
        return HttpResponseForbidden('Importing pullrequests is disabled')

    trigger_url = import_pullrequest_trigger_resource.get_uri(request)

    template = get_template('mozreview/import-pullrequest.html')
    return HttpResponse(template.render(Context({
        'request': request,
        'user': user,
        'repo': repo,
        'pullrequest': pullrequest,
        'trigger_url': trigger_url,
    })))

