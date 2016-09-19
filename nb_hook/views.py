from django.http import HttpResponse, Http404
from . import models, misc
from apis import sf_backends_staging as sf_backends
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

        for tag in content['payload']['person']['tags']:
            save_user(content, tag, 'created')

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

        for tag in content['payload']['person']['tags']:
            save_user(content, tag, 'updated')

    raise Http404("Not found")


def send_petition_user_to_sf(contact, campaign_name):
    """
    Parse the data received from Nationbuilder (via hook and save_update) and send to Salesforce via Force.com API

    @type contact: dict
    @type campaign_name: str

    Args:
        contact: contact dict from
        campaign_name: campaign name

    Returns:
        True if successful
    """
    person = contact['payload']['person']
    # set default language if none is selected
    if person['user_language'] is None:
        person['user_language'] = 'EN'

    try:
        if person['primary_address']['country_code'] == 'Other' or person['primary_address']['country_code'] == 'other':
            country_code = ''
        else:
            country_code = person['primary_address']['country_code']
    except:
        country_code = ''

    contact_obj = {
        'FirstName': person['first_name'],
        'LastName': person['last_name'],
        'Email': person['email'],
        'MailingCountryCode': country_code,
        'Subscriber__c': person['email_opt_in'],
        'Sub_Mozilla_Foundation__c': person['email_opt_in'],
        'Email_Language__c': person['user_language'],
        'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID_STG  # advocacy record type
        }

    if person['salesforce_id']:  # not used because we are not saving salesforce ID back
        sf_backends.update_user(person['salesforce_id'], contact_obj)
        sf_contact_id = {'id': person['salesforce_id']}
    else:
        sf_contact_id = sf_backends.insert_user(contact_obj)
        # nb_backends.nb_update_salesforce_id(person['id'], sf_contact_id['id'])  #disable to prevent record duplication
    
    #print sf_contact_id

    try:
        campaign_tag = models.Campaign.objects.get(nationbuilder_tag=campaign_name)
    except models.Campaign.DoesNotExist:
        campaign_tag = None
    if campaign_tag:
        dj_sf_campaign_id = campaign_tag.salesforce_id

        # add CampaignMember Obj
        sf_backends.upsert_contact_to_campaign({
            'ContactId': sf_contact_id['id'],
            'CampaignId': dj_sf_campaign_id,
            'Campaign_Language__c': person['user_language'],
            'Campaign_Email_Opt_In__c': person['email_opt_in'],
        })

    else:
        # add campaign obj to SalesForce
        sf_campaign_id = sf_backends.insert_campaign({
            'Name': campaign_name,
            'Type': 'Petition'
        })

        # save it in DJ NB -> SF model
        dj_campaign_obj = models.Campaign(
            nationbuilder_tag=campaign_name,
            salesforce_id=sf_campaign_id['id'],
        )
        dj_campaign_obj.save()

        # add CampaignMember Obj
        sf_backends.upsert_contact_to_campaign({
            'ContactId': sf_contact_id['id'],
            'CampaignId': sf_campaign_id['id'],
            'Campaign_Language__c': person['user_language'],
            'Campaign_Email_Opt_In__c': person['email_opt_in'],
        })

    return True


def send_event_user_to_sf(contact, campaign_name):
    """
    NOT USED
    Parse the data received from Nationbuilder (via hook and save_update) and send to Salesforce via Force.com API

    @type contact: dict
    @campaign_name: str

    Args:
        contact:

    Returns:
        True if successful
    """
    person = contact['payload']['person']

    # set default language if none is selected
    if person['user_language'] is None:
        person['user_language'] = 'EN'

    try:
        if person['primary_address']['country_code'] == 'Other' or person['primary_address']['country_code'] == 'other':
            country_code = ''
        else:
            country_code = person['primary_address']['country_code']
    except:
        country_code = ''

    contact_obj = {
        'FirstName': person['first_name'],
        'LastName': person['last_name'],
        'Email': person['email'],
        'MailingCountryCode': country_code,
        'Email_Language__c': person['user_language'],
        'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID_STG  # advocacy record type
    }

    if person['salesforce_id']:  # not used because we are not saving salesforce ID back
        sf_backends.update_user(person['salesforce_id'], contact_obj)
        sf_contact_id = {'id': person['salesforce_id']}
    else:
        sf_contact_id = sf_backends.insert_user(contact_obj)
        # nb_backends.nb_update_salesforce_id(person['id'], sf_contact_id['id'])  #disable to prevent record duplication

    # print sf_contact_id
    #
    # try:
    #     campaign_tag = models.Campaign.objects.get(nationbuilder_tag=campaign_name)
    # except models.Campaign.DoesNotExist:
    #     campaign_tag = None
    # if campaign_tag:
    #     dj_sf_campaign_id = campaign_tag.salesforce_id
    #
    #     # add CampaignMember Obj
    #     sf_backends.upsert_contact_to_campaign({
    #         'ContactId': sf_contact_id['id'],
    #         'CampaignId': dj_sf_campaign_id,
    #         'Campaign_Language__c': person['user_language'],
    #         'Campaign_Member_Type__c': "Host",
    #         'Attended_Before__c': person['attended'],
    #     })
    # else:
    #     # add campaign obj to SalesForce
    #     sf_campaign_id = sf_backends.insert_campaign({
    #         'Name': campaign_name,
    #         'Type': 'Event'
    #     })
    #
    #     # save it in DJ NB -> SF model
    #     dj_campaign_obj = models.Campaign(
    #         nationbuilder_tag=campaign_name,
    #         salesforce_id=sf_campaign_id['id'],
    #     )
    #     dj_campaign_obj.save()
    #
    #     # add CampaignMember Obj
    #     sf_backends.upsert_contact_to_campaign({
    #         'ContactId': sf_contact_id['id'],
    #         'CampaignId': sf_campaign_id['id'],
    #         'Campaign_Language__c': person['user_language'],
    #         'Campaign_Member_Type__c': "Host",
    #         'Attended_Before__c': person['attended'],
    #     })
    #
    return True


# @csrf_exempt
# def send_to_sf_event(contact):
#     """
#
#     Args:
#         contact:
#
#     Returns:
#
#     """
#
#     person = contact['payload']['person']
#
#     ### set default language if none is selected
#     if person['user_language'] is None:
#         person['user_language'] = 'EN'
#
#     try:
#         if person['primary_address']['country_code'] == 'Other' or person['primary_address']['country_code'] == 'other':
#             country_code = ''
#         else:
#             country_code = person['primary_address']['country_code']
#     except:
#         country_code = ''
#
#
#     contact_obj = {
#         'FirstName': person['first_name'],
#         'LastName': person['last_name'],
#         'Email': person['email'],
#         'MailingCountryCode': country_code,
#         # 'Subscriber__c': person['email_opt_in'],
#         # 'Sub_Mozilla_Foundation__c': person['email_opt_in'],
#         'Email_Language__c': person['user_language'],
#         'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID  # advocacy record type
#     }
#     if person['salesforce_id']:  # not used because we are not saving salesforce ID back
#         sf_backends.update_user(person['salesforce_id'], contact_obj)
#         sf_contact_id = {'id': person['salesforce_id']}
#     else:
#         sf_contact_id = sf_backends.insert_user(contact_obj)
#
#     attended = "No"
#
#     for campaign in person['tags']:
#         try:
#             campaign_tag = models.Campaign.objects.get(nationbuilder_tag=campaign)
#         except models.Campaign.DoesNotExist:
#             campaign_tag = None
#         if campaign_tag:
#             dj_sf_campaign_id = campaign_tag.salesforce_id
#
#             sf_backends.upsert_contact_to_campaign({
#                 'ContactId': sf_contact_id['id']
#                 'CampaignId': dj_sf_campaign_id,
#                 'Campaign_Language__c': person['user_language'],
#                 'Campaign_Member_Type__c': "Host",
#                 'Attended_Before__c': attended,
#             })
#         else:
#             ### add campaign obj to SalesForce
#             sf_campaign_id = sf_backends.insert_campaign({
#                 'Name': campaign,
#                 'Type': 'Event'
#             })
#
#             ### save it in DJ NB -> SF model
#             dj_campaign_obj = models.Campaign(
#                 nationbuilder_tag=campaign,
#                 salesforce_id=sf_campaign_id['id'],
#             )
#             dj_campaign_obj.save()
#
#             ### add CampaignMember Obj
#             sf_backends.upsert_contact_to_campaign({
#                 'ContactId': sf_contact_id['id']
#                 'CampaignId': dj_sf_campaign_id,
#                 'Campaign_Language__c': person['user_language'],
#                 'Campaign_Member_Type__c': "Host",
#                 'Attended_Before__c': attended,
#             })


def save_user(content, campaign_name, post_type):
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

    try:
        matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email']).update(contact=content, synced=False)
    except models.ContactSync.DoesNotExist:
        matching_contacts = None

    if matching_contacts:
        db_contact = models.ContactSync.objects.get(email=content['payload']['person']['email'])
    else:
        db_contact = models.ContactSync(email=content['payload']['person']['email'],
                                        contact=content,
                                        type=post_type)
        db_contact.save()

    if campaign_name == 'Copyright Campaign':
        saved = send_petition_user_to_sf(content, campaign_name)
    elif 'Maker Events' in campaign_name:
        saved = send_event_user_to_sf(content, campaign_name)

    #saved =  True #For testing
    if saved:
        db_contact.synced = True
        db_contact.save()
        return HttpResponse('saved')
    else:
        return HttpResponse('not saved')


# @csrf_exempt
# def save_petition_update(request):
#     """
#     Receive POST signal from Nationbuilder user changed webhook and add to Salesforce via send_to_sf method
#     Args:
#         request:
#
#     Returns:
#         HttpResponse
#     """
#
#     if request.method == "POST":
#         content = request.body
#         content = json.loads(content)
#
#         # save all data to a log table
#         log_contact = models.Log(
#             email=content['payload']['person']['email'],
#             contact=request.body,
#             type='updated',
#         )
#         log_contact.save()
#
#         # add this to prevent NB sending duplicated user_created with user_language as null
#         if not content['payload']['person']['user_language']:
#             return HttpResponse('not saved, no user_language')
#
#         # check NB token
#         if 'token' not in content:
#             raise Http404("Not found")
#         if content['token'] != settings.NB_TOKEN:
#             raise Http404("Not found")
#
#         try:
#             matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email']).update(contact=request.body, synced=False)
#         except models.ContactSync.DoesNotExist:
#             matching_contacts = None
#
#         if matching_contacts:
#             return HttpResponse('contact exist')
#         else:
#             update_obj = models.ContactSync(email=content['payload']['person']['email'],
#                                             contact=request.body,
#                                             type='updated')
#             update_obj.save()
#
#         saved = send_to_sf(content)
#         # saved =  True #For testing
#         if saved:
#             update_obj.synced = True
#             update_obj.save()
#             return HttpResponse('All contacts updated')
#         else:
#             return HttpResponse('no contacts found to be updated')
#
#     raise Http404("Not found")


# def save_event_user(request):
#     """
#     Receive POST signal from Nationbuilder user created for  webhook and add to Salesforce via send_to_sf method
#     Args:
#         request:
#
#     Returns:
#
#     """
#
#     if request.method == "POST":
#         content = request.body
#         content = json.loads(content)
#
#
#     # save all data to a log table
#     log_contact = models.MakerLog(
#         email=content['payload']['person']['email'],
#         contact=request.body,
#         type='updated',
#     )
#     log_contact.save()
#
#     # check NB token
#     misc.check_nb_token(content)
#
#     try:
#         matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email'])
#     except models.ContactSync.DoesNotExist:
#         matching_contacts = None
#
#     if matching_contacts:
#         return HttpResponse('contact exist')
#     else:
#         db_contact = models.ContactSync(email=content['payload']['person']['email'],
#                                         contact=request.body,
#                                         type='maker_created')
#         db_contact.save()
#
#     saved = send_to_sf(content)
#     # saved =  True #For testing
#     if saved:
#         db_contact.synced = True
#         db_contact.save()
#         return HttpResponse('saved')
#     else:
#         return HttpResponse('not saved')
#
#
#     raise Http404("Not found")






# @csrf_exempt
# def update(request):
#     """
#     NOT USED
#
#     """
#     ### check if there is any duplicate entries due to NB
#     # try:
#         # contacts = models.ContactSync.objects
#
#     try:
#         max_time = timezone.now() - timezone.timedelta(minutes=1) #the newest selected field must be at least 1 minutes old which is the time that salesforce need
#         #print timezone.now()
#         #print max_time
#         contacts = models.ContactSync.objects.filter(synced=False, created_at__lte=max_time).order_by('-created_at')
#     except models.ContactSync.DoesNotExist:
#         contacts = None
#     if contacts:
#         for contact_item in contacts:
#             #print contact_item.contact
#             content = contact_item.contact
#             content = json.loads(content)
#             #print content
#             try:
#                 sent_to_sf = send_to_sf(content)
#             except:
#                 sent_to_sf = None
#             #sent_to_sf = True #For debug without send to salesforce
#             if sent_to_sf:
#                 contact_item.synced = True
#                 contact_item.save()
#         return HttpResponse('All contacts updated')
#     else:
#         return HttpResponse('no contacts found to be updated')
