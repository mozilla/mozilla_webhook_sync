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


def fetch_campaign(object_id):
    sf = get_sf_session()
    return sf.Campaign.get(object_id)


def fetch_campaign_by_name(name):
    sf = get_sf_session()
    query = "select id from Campaign where Name = '{0}'".format(name)
    return sf.query_all(query)


def insert_campaign(object):
    sf = get_sf_session()
    return sf.Campaign.create(object)


def insert_contact_to_campaign(object):
    sf = get_sf_session()
    return sf.CampaignMember.create(object)
