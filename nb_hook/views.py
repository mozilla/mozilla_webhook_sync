from django.http import HttpResponse, Http404
from . import models, misc
from apis import sf_backends
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings


@csrf_exempt
def create_hook(request):
    """
    Entry point of Nationbuilder POSTs, check the Nationbuilder POST belongs to Copyright Petition or Maker Event

    @type request: class

    Args:
        content:

    Returns:
        Nothing

    """

    if request.method == "POST":
        content = request.body
        content = json.loads(content)

        misc.check_nb_token(content)

        save_user(content, 'created')

    raise Http404("Not found")


@csrf_exempt
def update_hook(request):
    """
    Entry point of Nationbuilder POSTs, check the Nationbuilder POST belongs to Copyright Petition or Maker Event

    @type request: object

    Args:
        content:

    Returns:

    """
    if request.method == "POST":
        content = request.body
        content = json.loads(content)

        misc.check_nb_token(content)

        save_user(content, 'updated')

    raise Http404("Not found")


def save_user(content, post_type):
    """
    Receive POST signal from Nationbuilder user created webhook and add to Salesforce via send_to_sf method

    @type content: dict
    @type campaign_name: str
    @type post_type: str

    Args:
        request:

    Returns:
        HttpResponse
    """


    # save all data to a log table
    log_contact = models.Log(
        email=content['payload']['person']['email'],
        contact=content,
        type=post_type,
    )
    log_contact.save()

    # add this to prevent NB sending duplicated user_created with user_language as null
    if not content['payload']['person']['user_language']:
        return HttpResponse('not saved, no user_language')

    if 'Copyright Campaign' not in content['payload']['person']['tags']:
        return HttpResponse('Not Copyright Petition')

    try:
        matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email']).update(contact=content, synced=False)
    except models.ContactSync.DoesNotExist:
        matching_contacts = None

    if matching_contacts:
        pass
    else:
        db_contact = models.ContactSync(email=content['payload']['person']['email'],
                                        contact=content,
                                        type=post_type)
        db_contact.save()

    return HttpResponse('saved')
