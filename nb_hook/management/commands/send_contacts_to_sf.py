from django.core.management.base import BaseCommand
from django.conf import settings
from apis import sf_backends
from apis.sf_backends import check_count
from nb_hook.models import *
from events.sync import determine_country_code, determine_user_language
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Check API upper limit")
        if not check_count():
            return

        print("Begin sending contacts to Salesforce")

        # fetch un-synced contacts from database
        contact_list = ContactSync.objects.filter(synced=False, id__gte=58512).order_by('created_at')[:500]
        # sync them to salesforce
        for contact in contact_list:
            if not check_count():
                print("Daily limit reached")
                return

            print("----------")

            try:
                person_obj = eval(contact.contact)
            except:
                person_obj = json.loads(contact.contact)

            person = person_obj['payload']['person']
            print(person['email'])
            try:
                contact_obj = {
                    'FirstName': person['first_name'][:40],
                    'LastName': person['last_name'][:80],
                    'Email': person['email'],
                    'MailingCountryCode': determine_country_code(person_obj['payload']),
                    'Email_Language__c': determine_user_language(person_obj['payload']),
                    'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID,  # advocacy record type
                    'Signup_Source_URL__c': 'changecopyright.org',
                }
                sf_contact_id = sf_backends.insert_user(contact_obj)
                print("sf_contact_id")
                print(sf_contact_id['id'])
            except:
                print("Contact is having error")
                continue

            try:
                sf_backends.upsert_contact_to_campaign({
                    'ContactId': sf_contact_id['id'],
                    'CampaignId': settings.SF_PETITION_CAMPAIGN_ID,
                    'Campaign_Language__c': person['user_language'],
                    'Campaign_Email_Opt_In__c': person['email_opt_in'],
                })
                print("added to CampaignMember")
            except:
                print("CampaignMember NOT added")

            contact.synced = True
            contact.save()

        print("Done Syncing")
