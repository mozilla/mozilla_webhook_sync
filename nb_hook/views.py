from django.http import HttpResponse, Http404
from . import sf_backends, nb_backends, models
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def hook(request):
    if request.method == "POST":

        content = request.body
        content = json.loads(content)
        person = content['payload']['person']
        contact_obj = {
            'FirstName': person['first_name'],
            'LastName': person['last_name'],
            'Email': person['email'],
            'MailingCountryCode': person['primary_address']['country_code'],
        }

        if person['salesforce_id']:
            sf_backends.upsert_user(person['salesforce_id'], contact_obj)
        else:
            sf_contact_id = sf_backends.insert_user(contact_obj)
            nb_backends.nb_update_salesforce_id(person['id'], sf_contact_id['id'])

        for campaign in person['tags']:
            campaign_tag = models.Campaign.objects.get(nationbuilder_tag=campaign)
            if campaign_tag:
                dj_sf_campaign_id = campaign_tag.salesforce_id

                # add CampaignMember Obj
                sf_backends.insert_contact_to_campaign({
                    'ContactId': sf_contact_id['id'],
                    'CampaignId': dj_sf_campaign_id,
                })
            else:
                # add campaign obj to SalesForce
                sf_campaign_id = sf_backends.insert_campaign({
                    'Name': campaign
                })

                # save it in DJ NB -> SF model
                dj_campaign_obj = models.Campaign(
                    nationbuilder_tag=campaign,
                    salesforce_id=sf_campaign_id['id'],
                )
                dj_campaign_obj.save()

                # add CampaignMember Obj
                sf_backends.insert_contact_to_campaign({
                    'ContactId': sf_contact_id['id'],
                    'CampaignId': sf_campaign_id['id'],
                })

        return HttpResponse('saved')

    # campaign = sf_backends.insert_campaign({'Name': 'Test Campaign2'})
    # print sf_backends.insert_contact_to_campaign({
    #     'ContactId': '00321000007AbZ3',
    #     'CampaignId': '701210000001rXFAAY'
    # })
    # print sf_backends.fetch_campaign('00v21000000TLKa')
    # return HttpResponse('stuff')
    raise Http404("Not found")
