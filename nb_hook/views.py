from django.http import HttpResponse, Http404
from . import sf_backends, nb_backends
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def hook(request):
    if request.method == "POST":
        content = request.body
        content = json.loads(content)
        person = content['payload']['person']
        insert_object = {
            'FirstName': person['first_name'],
            'LastName': person['last_name'],
            'Email': person['email'],
            'Subscriber__c': person['email_opt_in'],
            'MailingCountryCode': person['primary_address']['country_code'],
            'MailingPostalCode': person['primary_address']['zip'],
        }
        if person['salesforce_id']:
            sf_backends.upsert_user(person['salesforce_id'], insert_object)
        else:
            sf_id = sf_backends.insert_user(insert_object)
            nb_backends.nb_update_salesforce_id(person['id'], sf_id['id'])

        return HttpResponse('saved')

    raise Http404("Not found")
