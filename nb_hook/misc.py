from django.http import Http404
from django.conf import settings


def check_nb_token(content):
    """
    Check Nationbuilder Token, if not found or not matching settings, raise 404
    Args:
        content:

    Returns:
        Raise 404 if error
    """
    if 'token' not in content:
        raise Http404("Not found")
    if content['token'] != settings.NB_TOKEN:
        raise Http404("Not found")