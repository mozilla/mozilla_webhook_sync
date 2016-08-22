from simple_salesforce import Salesforce
import requests
from django.conf import settings


def get_sf_session():
    session = requests.Session()
    return Salesforce(username=settings.SF_USERNAME,
                      password=settings.SF_PASSWORD,
                      security_token=settings.SF_TOKEN,
                      sandbox=settings.SF_SANDBOX,
                      session=session,
                      )


def fetch_user(object_id):
    sf = get_sf_session()
    return sf.Contact.get(object_id)


def insert_user(object):
    sf = get_sf_session()
    return sf.Contact.create(object)


def upsert_user(object_id, object):
    sf = get_sf_session()
    return sf.Contact.upsert(object_id, object)
