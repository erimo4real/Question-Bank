from urllib.parse import urlencode

from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def is_new(created_at, days=7):
    if not created_at:
        return False
    return (timezone.now() - created_at).days < days


@register.simple_tag(takes_context=True)
def append_page(context, page_number):
    request = context["request"]
    params = request.GET.copy()
    params["page"] = page_number
    return f"?{params.urlencode()}"
