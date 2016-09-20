from django.shortcuts import render
from django.http import HttpResponse, Http404
from apis import nb_backends, sf_backends_staging as sf_backends
from models import *
from annoying.functions import get_object_or_None
from django.utils import timezone
from django.conf import settings

import json
# Create your views here.


# def fetch_last_sync_datetime():
#     return LastSync.objects.get(id=1)
#
#
# def update_last_sync_datetime():
#     obj = LastSync(last_sync=timezone.now)
#     obj.save()
#     return obj


# def get_person_info(request):
#     print (sf_backends.fetch_user('00321000007r4sW'))
#     return HttpResponse('test')

def run(request):
    """
    URL to run the sync
    Args:
        request: class

    Returns:
        HttpResponse
    """
    if request.method == "GET":
        token = request.GET.get('token')
        if token != settings.NB_TOKEN:
            return Http404('not found')

    event_list = nb_backends.fetch_events().json()
    for event in event_list['results']:
        event_dj = fetch_save_event(event)
        if event_dj is not False:
            record_campaign_members(event['id'])
    # update_last_sync_datetime()
    return HttpResponse('done')


def fetch_save_event(event):
    """
    Fetch events from Nationbuilder (with heroku schedular syncing every 10 minutes because webhook does not provide it

    @type event: dict

    Args:
        event: event

    Returns:

    """

    # check if event exists in Salesforce
    event_dj = get_object_or_None(Campaign, nb_id=event['id'])
    if not event_dj:
        # fetch creator user nb_id from Nationbuilder via author_id in event obj
        if event['author_id'] is None:
            return False
        creator = nb_backends.fetch_user(event['author_id']).json()
        user_language = determine_user_language(creator)
        country_code = determine_country_code(creator)

        # create or update creator user fb_id from Salesforce via email from event obj
        try:
            creator_sf_id = sf_backends.insert_user({
                'FirstName': creator['person']['first_name'],
                'LastName': creator['person']['last_name'],
                'Email': creator['person']['email'],
                # 'MailingStreet': creator['person']['primary_address']['address1'],
                # 'MailingCity': creator['person']['primary_address']['city'],
                # 'MailingState': creator['person']['primary_address']['state'],
                # 'MailingPostalCode': creator['person']['primary_address']['zip'],
                # 'MailingStateCode': creator['person']['primary_address']['state'],
                'MailingCountryCode': country_code,

                'Email_Language__c': user_language,
                'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID_STG  # advocacy record type
            })
        except:
            return False

        # insert campaign to SF and get the sf_campaign_id
        event_sf_obj = {
            'Name': 'Maker Events - ' + event['name'],
            'Type': 'Event',
            'Location__c': insert_address(event)

        }
        try:
            sf_campaign_id = sf_backends.insert_campaign(event_sf_obj)

            # save obj to DJ Campaign table
            event_dj_obj = Campaign(
                name=event['name'],
                start_time=event['start_time'],
                nb_id=event['id'],
                sf_id=sf_campaign_id['id'],
                type='Event',
                creator_sf_id=creator_sf_id['id'],
            )
            event_dj_obj.save()
        except:
            return False
    else:
        event_dj_obj = {
            'name': event_dj.name,
            'start_time':  event_dj.start_time,
            'nb_id': event_dj.nb_id,
            'sf_id': event_dj.sf_id,
            'type': event_dj.type,
            'creator_sf_id': event_dj.creator_sf_id
        }
        # event_dj_obj = event_dj

    return event_dj_obj


def record_campaign_members(event_nb_id):
    """
    Fetch event RSVPs from NB (campaign_members_nb_list) and compare the list with Django and Salesforce, if records
    do not exist in Django and Salesforce, insert them to both.

    @type event_nb_id: int

    Args:
        event_nb_id: Event ID from Nationbuilder

    Returns:
        None
    """

    # fetch campaign_member_rsvps from NB
    campaign_members_nb_list = nb_backends.fetch_event_rsvps(event_nb_id).json()

    # compare with existing data from Django, if it is not there, save it in Django and then send it to Salesforce.
    compare_nb_dj_member_list(campaign_members_nb_list['results'])

    return HttpResponse('done recording campaign_members')


def compare_nb_dj_member_list(nb_list):
    for nb_member in nb_list:
        if not CampaignMember.objects.filter(member_nb_id=nb_member['person_id']).exists():
            user_details = nb_backends.fetch_user(nb_member['person_id']).json()

            event_dj = get_object_or_None(Campaign, nb_id=nb_member['event_id'])

            user_language = determine_user_language(user_details)
            country_code = determine_country_code(user_details)

            try:
                sf_contact_id = sf_backends.insert_user({
                    'FirstName': user_details['person']['first_name'],
                    'LastName': user_details['person']['last_name'],
                    'Email': user_details['person']['email'],
                    # 'MailingStreet': user_details['person']['primary_address']['address1'],
                    # 'MailingCity': user_details['person']['primary_address']['city'],
                    # 'MailingState': user_details['person']['primary_address']['state'],
                    # 'MailingPostalCode': user_details['person']['primary_address']['zip'],
                    'MailingCountryCode': country_code,
                    'Email_Language__c': user_language,
                    'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID_STG  # advocacy record type
                })
            except:
                continue

            obj = CampaignMember(
                campaign_id=event_dj,
                member_sf_id=sf_contact_id['id'],
                member_nb_id=nb_member['person_id'],
                attended_before=False,
                campaign_language=user_language
            )
            obj.save()

            sf_backends.upsert_contact_to_campaign({
                'ContactId': sf_contact_id['id'],
                'CampaignId': event_dj.sf_id,
                'Campaign_Language__c': user_details['person']['user_language'],
                'Campaign_Member_Type__c': "Attendee",
                'Attended_Before__c': 'no',
            })


def determine_country_code(nb_person_obj):
    try:
        if nb_person_obj['person']['primary_address']['country_code'] == 'Other' or \
                        nb_person_obj['person']['primary_address']['country_code'] == 'other':
            country_code = ''
        else:
            country_code = nb_person_obj['person']['primary_address']['country_code']
    except:
        country_code = ''

    return country_code


def insert_address(obj):
    if 'venue' not in obj:
        return ''
    else:
        nb_address = obj['venue']['address']

    address = ''
    if 'name' in obj['venue']:
        try:
            address = obj['venue']['name'] + ', '
        except:
            pass
    if 'address1' in nb_address:
        try:
            address = nb_address['address1'] + ', '
        except:
            pass
    if 'address2' in nb_address:
        try:
            address = address + nb_address['address2'] + ', '
        except:
            pass
    if 'city' in nb_address:
        try:
            address = address + nb_address['city'] + ', '
        except:
            pass
    if 'state' in nb_address:
        try:
            address = address + nb_address['state'] + ', '
        except:
            pass
    if 'zip' in nb_address:
        try:
            address = address + nb_address['zip'] + ', '
        except:
            pass
    if 'country' in nb_address:
        try:
            address = address + nb_address['country_code']
        except:
            pass
    return address


def determine_user_language(nb_person_obj):
    if 'user_language' not in nb_person_obj['person'] or nb_person_obj['person']['user_language'] is None:
        return 'EN'
    else:
        return nb_person_obj['person']['user_language']
