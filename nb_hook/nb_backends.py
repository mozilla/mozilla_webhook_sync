from rauth import OAuth2Service
from django.conf import settings
import json
import requests


def nb_update_salesforce_id(person_id, salesforce_id):
    nation_slug = settings.NB_NATION_SLUG

    def endpoint(endpoint):
        return 'https://' + nation_slug + ".nationbuilder.com/api/v1/" + endpoint

    params = {
        "access_token": settings.NB_API_KEY
    }
    person = {
        'person': {
            'salesforce_id': salesforce_id
        }
    }
    return requests.put(endpoint('people/'+str(person_id)), params=params, json=person)
