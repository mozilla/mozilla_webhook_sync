from django.http import HttpResponse, Http404
from . import sf_backends, nb_backends, models
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import time
from django.conf import settings


@csrf_exempt
def send_to_sf(contact):
    person = contact['payload']['person']

    ### for testing ONLY and temporarily saving data to db
    # test_obj = models.TestHook(content=request.body)
    # test_obj.save()

    ### set default language if none is selected
    if person['user_language'] is None:
        person['user_language'] = 'EN'
    
    if person['primary_address']['country_code'] == 'other' :
        person['primary_address']['country_code'] = ''

    contact_obj = {
        'FirstName': person['first_name'],
        'LastName': person['last_name'],
        'Email': person['email'],
        'MailingCountryCode': person['primary_address']['country_code'],
        'Subscriber__c': person['email_opt_in'],
        'Sub_Mozilla_Foundation__c': person['email_opt_in'],
        'Email_Language__c': person['user_language'],
        'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID  # advocacy record type
    }
    if person['salesforce_id']:  # not used because we are not saving salesforce ID back
        sf_backends.update_user(person['salesforce_id'], contact_obj)
        sf_contact_id = {'id': person['salesforce_id']}
    else:
        sf_contact_id = sf_backends.insert_user(contact_obj)
        # nb_backends.nb_update_salesforce_id(person['id'], sf_contact_id['id'])  #disable to prevent record duplication
    
    #print sf_contact_id
    
    for campaign in person['tags']:
        try:
            campaign_tag = models.Campaign.objects.get(nationbuilder_tag=campaign)
        except models.Campaign.DoesNotExist:
            campaign_tag = None
        if campaign_tag:
            dj_sf_campaign_id = campaign_tag.salesforce_id

            ### add CampaignMember Obj
            sf_backends.upsert_contact_to_campaign({
                'ContactId': sf_contact_id['id'],
                'CampaignId': dj_sf_campaign_id,
                'Campaign_Language__c': person['user_language'],
                'Campaign_Email_Opt_In__c': person['email_opt_in'],
            })
        else:
            ### add campaign obj to SalesForce
            sf_campaign_id = sf_backends.insert_campaign({
                'Name': campaign,
                'Type': 'Petition'
            })

            ### save it in DJ NB -> SF model
            dj_campaign_obj = models.Campaign(
                nationbuilder_tag=campaign,
                salesforce_id=sf_campaign_id['id'],
            )
            dj_campaign_obj.save()

            ### add CampaignMember Obj
            sf_backends.upsert_contact_to_campaign({
                'ContactId': sf_contact_id['id'],
                'CampaignId': sf_campaign_id['id'],
                'Campaign_Language__c': person['user_language'],
                'Campaign_Email_Opt_In__c': person['email_opt_in'],
            })
    return True


@csrf_exempt
def hook(request):
    if request.method == "POST":
        content = request.body
        content = json.loads(content)

        ### check NB token
        if 'token' not in content:
            raise Http404("Not found")
        if content['token'] != settings.NB_TOKEN:
            raise Http404("Not found")
        
        try: 
            matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email'])
        except models.ContactSync.DoesNotExist:
            matching_contacts = None

        if matching_contacts:
            return HttpResponse('contact exist')
        else:
            db_contact = models.ContactSync(email=content['payload']['person']['email'], contact=request.body)
            db_contact.save()

        saved = send_to_sf(content)
        #saved =  True #For testing
        if saved:
            db_contact.synced = True
            db_contact.save()
            return HttpResponse('saved')
        else:
            return HttpResponse('not saved')
    raise Http404("Not found")


@csrf_exempt
def update(request):
    try:
        max_time = timezone.now() - timezone.timedelta(minutes=1) #the newest selected field must be at least 1 minutes old which is the time that salesforce need
        #print timezone.now()
        #print max_time
        contacts = models.ContactSync.objects.filter(synced=False, created_at__lte=max_time).order_by('-created_at')
    except models.ContactSync.DoesNotExist:
        contacts = None
    if contacts: 
        for contact_item in contacts:
            #print contact_item.contact
            content = contact_item.contact
            content = json.loads(content)
            #print content
            sent_to_sf =  send_to_sf(content)
            #sent_to_sf = True #For debug without send to salesforce
            if sent_to_sf:
                contact_item.synced = True
                contact_item.save()
        return HttpResponse('All contacts updated')
    else:
        return HttpResponse('no contacts found to be updated')


@csrf_exempt
def save_update(request):
    if request.method == "POST":
        content = request.body
        content = json.loads(content)

        ### check NB token
        if 'token' not in content:
            raise Http404("Not found")
        if content['token'] != settings.NB_TOKEN:
            raise Http404("Not found")

        try: 
            matching_contacts = models.ContactSync.objects.filter(email=content['payload']['person']['email'])
        except models.ContactSync.DoesNotExist:
            matching_contacts = None

        if matching_contacts:
            matching_contacts = models.ContactSync(email=content['payload']['person']['email'],
                                            contact=request.body,
                                            synced=False)
            matching_contacts.save()
            return HttpResponse('contact exist')
        else:
            update_obj = models.ContactSync(email=content['payload']['person']['email'], contact=request.body)
            update_obj.save()
            return HttpResponse('saved')

    raise Http404("Not found")
