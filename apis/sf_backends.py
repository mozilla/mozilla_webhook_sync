from simple_salesforce import Salesforce
import requests
from django.conf import settings
import re


def get_sf_session():
    session = requests.Session()

    if settings.SF_SANDBOX == 'true':
        sandbox = True
    else:
        sandbox = False

    return Salesforce(username=settings.SF_USERNAME,
                      password=settings.SF_PASSWORD,
                      security_token=settings.SF_TOKEN,
                      sandbox=sandbox,
                      session=session,
                      )


def fetch_user(object_id):
    sf = get_sf_session()
    return sf.Contact.get(object_id)


def fetch_user_by_email(email):
    sf = get_sf_session()
    query = "select id from Contact where Email = '{0}'".format(email)
    return sf.query_all(query)


def insert_user(object):
    sf = get_sf_session()

    # search for existing user
    query = "select Id from Contact where Email = '{0}'".format(object['Email'])
    results = sf.query_all(query)
    try:
        object_id = results['records'][0]['Id']
        print 'heres the stuff'
    except:
        object_id = None

    if object_id is not None:
        sf.Contact.update(object_id, object)
        print 'heres the stuff again'
        print object_id
        return {'id': object_id}
    else:
        return sf.Contact.create(object)


def update_user(object_id, object):
    sf = get_sf_session()
    return sf.Contact.update(object_id, object)


def fetch_campaign(object_id):
    sf = get_sf_session()
    return sf.Campaign.get(object_id)


def fetch_campaign_by_name(name):
    sf = get_sf_session()
    query = "select id from Campaign where Name = '{0}'".format(re.sub(r"([\'])", r'\\\1', name))
    return sf.query_all(query)


def insert_campaign(object):
    sf = get_sf_session()
    query = "select id from Campaign where Nationbuilder_id__c = '{0}'".format(object['Nationbuilder_id__c'])
    results = sf.query_all(query)
    try:
        object_id = results['records'][0]['Id']
    except:
        object_id = None

    if object_id is not None:
        sf.Campaign.update(object_id, object)
        return {'id': object_id}
    else:
        return sf.Campaign.create(object)


def delete_campaign(object_id):
    sf = get_sf_session()
    try:
        return sf.Campaign.delete(object_id)
    except:
        return False


def upsert_contact_to_campaign(object):
    sf = get_sf_session()

    # search for existing user
    query = "select id from CampaignMember where ContactId = '{0}' " \
            "and CampaignId = '{1}'".format(object['ContactId'], re.sub(r"([\'])", r'\\\1', object['CampaignId']))
    results = sf.query_all(query)
    try:
        object_id = results['records'][0]['Id']
    except:
        object_id = None

    if object_id is not None:
        object = {
            'Campaign_Language__c': object['Campaign_Language__c']
        }
        return sf.CampaignMember.update(object_id, object)
    else:
        return sf.CampaignMember.create(object)


def fetch_campaign_member(object_id):
    sf = get_sf_session()
    return sf.CampaignMember.get(object_id)


def upsert_campaign(object):
    sf = get_sf_session()

    query = "select id from Campaign where Name = '{0}'".format(re.sub(r"([\'])", r'\\\1', object['Name']))
    results = sf.query_all(query)

    try:
        object_id = results['records'][0]['Id']
    except:
        object_id = None

    if object_id is not None:
        sf.Campaign.update(object_id, object)
        return {'id': object_id}
    else:
        return sf.Campaign.create(object)
