from django import template


register = template.Library()


@register.assignment_tag(takes_context=True)
def get_full(context):
    request = context['request']
    return bool(request.GET.get('full'))
