from django.conf import settings
import requests


nation_slug = settings.NB_NATION_SLUG
params = {
    "access_token": settings.NB_API_KEY
}


def get_endpoint(endpoint):
    return requests.get('https://' + nation_slug + ".nationbuilder.com/api/v1/" + endpoint, params=params)


def post_endpoint(endpoint, json):
    return requests.post('https://' + nation_slug + ".nationbuilder.com/api/v1/" + endpoint, params=params, json=json)


def put_endpoint(endpoint, json):
    return requests.put('https://' + nation_slug + ".nationbuilder.com/api/v1/" + endpoint, params=params, json=json)


def nb_update_salesforce_id(person_id, salesforce_id):
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


def fetch_user(person_id):
    return get_endpoint('people/'+str(person_id))


def fetch_events():
    return get_endpoint('sites/makerevents/pages/events?limit=5000')


def fetch_event_rsvps(event_id):
    return get_endpoint('sites/makerevents/pages/events/{0}/rsvps?limit=5000'.format(event_id))
