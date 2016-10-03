from apis import nb_backends, sf_backends
from models import *
from annoying.functions import get_object_or_None
from django.utils import timezone
from django.conf import settings
import unicodedata


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

    # fetch creator user nb_id from Nationbuilder via author_id in event obj
    if event['author_id'] is None:
        return False
    creator = nb_backends.fetch_user(event['author_id']).json()
    user_language = determine_user_language(creator)
    country_code = determine_country_code(creator)

    if not event_dj:
        # create or update creator user fb_id from Salesforce via email from event obj
        try:
            creator_sf_id = sf_backends.insert_user({
                'FirstName': creator['person']['first_name'],
                'LastName': creator['person']['last_name'],
                'Email': creator['person']['email'],
                'MailingCountryCode': country_code,
                'Email_Language__c': user_language,
                'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID,  # advocacy record type
                'Subscriber__c': creator['person']['email_opt_in'],
                'Sub_Maker_Party__c': creator['person']['email_opt_in'],
                'Signup_Source_URL__c': 'makerparty.community',
            })
        except:
            return False

        # insert campaign to SF and get the sf_campaign_id
        event_sf_obj = {
            'Name': event['name'],
            'Type': 'Event',
            'Location__c': insert_address(event),
            'ParentId': settings.EVENT_PARENT_ID,
            'IsActive': True,
            'Nationbuilder_id__c': event['id'],
        }

        try:
            sf_campaign_id = sf_backends.insert_campaign(event_sf_obj)
            event_nb = nb_backends.fetch_event(event['id']).json()

            # save obj to DJ Campaign table
            event_dj_obj = Campaign(
                name=event['name'],
                start_time=event['start_time'],
                nb_id=event['id'],
                sf_id=sf_campaign_id['id'],
                type='Event',
                creator_sf_id=creator_sf_id['id'],
                content=event_nb['event'],
                parent_id=settings.EVENT_PARENT_ID,
                active=True,
            )
            event_dj_obj.save()

            nb_backends.save_event_sf_id(event['id'], sf_campaign_id['id'])

            # insert creator to CampaignMember and set them as "Host"
            sf_backends.upsert_contact_to_campaign({
                'ContactId': creator_sf_id['id'],
                'CampaignId': sf_campaign_id['id'],
                'Campaign_Language__c': user_language,
                'Campaign_Member_Type__c': "Host",
                'Attended_Before__c': 'no',
                'Campaign_Email_opt_in__c': creator['person']['email_opt_in'],
            })

        except:
            print 'error'
            return False
    else:
        # if event was updated less than 30 minutes ago, skip it
        if event_dj.sync_time > timezone.now() - timezone.timedelta(minutes=30):
            return False

        event_nb = nb_backends.fetch_event(event_dj.nb_id).json()
        if event_nb != event:
            event_sf_obj = {
                'Name': event['name'],
                'Type': 'Event',
                'Location__c': insert_address(event),
                'ParentId': settings.EVENT_PARENT_ID,
                'IsActive': True,
                'Nationbuilder_id__c': event['id'],
            }
            sf_campaign_id = sf_backends.insert_campaign(event_sf_obj)

            sf_backends.upsert_contact_to_campaign({
                'ContactId': event_dj.creator_sf_id,
                'CampaignId': sf_campaign_id['id'],
                'Campaign_Language__c': user_language,
                'Campaign_Member_Type__c': "Host",
                'Attended_Before__c': 'no',
                'Campaign_Email_opt_in__c': creator['person']['email_opt_in'],
            })

            event_dj_obj = {
                'name': event_nb['event']['name'],
                'start_time': event_nb['event']['start_time'],
                'type': event_dj.type,
                'creator_sf_id': event_dj.creator_sf_id,
                'content': event_nb['event'],
            }
            event_dj.name = event_nb['event']['name']
            event_dj.start_time = event_nb['event']['start_time']
            event_dj.content = event_nb['event']
            event_dj.sync_time = timezone.now()
            event_dj.save()
        else:
            event_dj.sync_time = timezone.now()
            event_dj.save()
            event_dj_obj = {
                'name': event_dj.name,
                'start_time':  event_dj.start_time,
                'nb_id': event_dj.nb_id,
                'sf_id': event_dj.sf_id,
                'type': event_dj.type,
                'creator_sf_id': event_dj.creator_sf_id,
                'content': event_nb,
            }

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

    print ("done recording campaign_members")


def compare_nb_dj_member_list(nb_list):
    for nb_member in nb_list:
        if not CampaignMember.objects.filter(member_nb_id=nb_member['person_id'], campaign_id_id=nb_member['event_id']).exists():
            user_details = nb_backends.fetch_user(nb_member['person_id']).json()
            event_dj = get_object_or_None(Campaign, nb_id=nb_member['event_id'])

            user_language = determine_user_language(user_details)
            country_code = determine_country_code(user_details)

            try:
                sf_contact_id = sf_backends.insert_user({
                    'FirstName': user_details['person']['first_name'],
                    'LastName': user_details['person']['last_name'],
                    'Email': user_details['person']['email'],
                    'MailingCountryCode': country_code,
                    'Email_Language__c': user_language,
                    'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID,  # advocacy record type
                    'Subscriber__c': user_details['person']['email_opt_in'],
                    'Sub_Maker_Party__c': user_details['person']['email_opt_in'],
                    'Signup_Source_URL__c': 'makerparty.community',
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
            try:
                sf_backends.upsert_contact_to_campaign({
                    'ContactId': sf_contact_id['id'],
                    'CampaignId': event_dj.sf_id,
                    'Campaign_Language__c': user_details['person']['user_language'],
                    'Campaign_Member_Type__c': "Attendee",
                    'Attended_Before__c': 'no',
                    'Campaign_Email_opt_in__c': user_details['person']['email_opt_in'],
                })
            except:
                continue


def remove_campaign(nb_id):
    campaign = Campaign.objects.get(nb_id=nb_id)
    sf_backends.delete_campaign(campaign.sf_id)
    return Campaign.objects.filter(nb_id=nb_id).update(active=False, sync_time=timezone.now())


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
        nb_address = (obj['venue']['address'])

    address = ''
    if 'name' in obj['venue']:
        try:
            address = (obj['venue']['name'] + ', ')
        except:
            pass
    try:
        if nb_address['address1'] != "":
            address = (address + nb_address['address1'] + ', ')
    except:
        pass
    try:
        if nb_address['address2'] != "":
            address = (address + nb_address['address2'] + ', ')
    except:
        pass
    try:
        if nb_address['city'] != "":
            address = (address + nb_address['city'] + ', ')
    except:
        pass
    try:
        if nb_address['state'] != "":
            address = (address + nb_address['state'] + ', ')
    except:
        pass
    try:
        if nb_address['zip'] != "":
            address = (address + nb_address['zip'] + ', ')
    except:
        pass
    try:
        if nb_address['country_code'] != "":
            address = (address + nb_address['country_code'])
    except:
        pass
    address = address.strip()
    address = address.strip(',')
    return address


def determine_user_language(nb_person_obj):
    if 'user_language' not in nb_person_obj['person'] or nb_person_obj['person']['user_language'] is None:
        return 'EN'
    else:
        return nb_person_obj['person']['user_language']
