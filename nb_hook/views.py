from django.http import HttpResponse, Http404
from . import sf_backends, nb_backends, models
from django.views.decorators.csrf import csrf_exempt
import json
import time
from django.conf import settings


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

        person = content['payload']['person']

        ### for testing ONLY and temporarily saving data to db
        # test_obj = models.TestHook(content=request.body)
        # test_obj.save()

        ### set default language if none is selected
        if person['user_language'] is None:
            person['user_language'] = 'EN'

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
        if person['salesforce_id']:
            sf_backends.update_user(person['salesforce_id'], contact_obj)
            sf_contact_id = {'id': person['salesforce_id']}
        else:
            sf_contact_id = sf_backends.insert_user(contact_obj)
            # nb_backends.nb_update_salesforce_id(person['id'], sf_contact_id['id'])  #disable to prevent record duplication

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

        return HttpResponse('saved')

    raise Http404("Not found")

@csrf_exempt
def update(request):
    if request.method == "POST":
        time.sleep(60)
        return hook(request)

    raise Http404("Not found")
