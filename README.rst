##########################################################
Mozilla Foundation Nationbuilder to SalesForce Sync Module
##########################################################

.. contents::
.. section-numbering::
.. raw:: pdf

    PageBreak oneColumn

==========================
Set up local settings file
==========================

Clone settings/local-dist and rename it to settings/local.py

Virtual Env
-----------

We recommend using Virtualenvs for settings up the dev enviornment. You will have to download "Virtual Env" (Venv) to set up an isolated environment for the applicaiton. You can download and install that by running::

  pip install virtualenv
  cd mozilla_webhook_sync
  virtualenv venv
  source venv/bin/activate

You will see (venv) in the beginning of every command line. That means the directory is currently wrapped inside the virtual environment "venv".

You will then need to install all the dependencies, by running::

  pip install -r requirements.txt

To run local dev server, run::

  python manage.py runserver --settings=settings.local

Please note that first time you will also need to run "migrate" command as well::

  python manage.py migrate --settings=settings.local


===============
Heroku Settings
===============

**Config Variables**

Many of the system settings are set via Heroku, you can get there via:

*settings* -> *Config Variables*

.. image:: https://github.com/mozilla/mozilla_webhook_sync/blob/master/readme/heroku_config_vars.png?raw=true

**Scheduler**

Heroku Scheduler is a plugin for running cron jobs, you can set the settings via:

*Overview* -> *Installed add-ons* -> *Heroku Scheduler*

.. image:: https://github.com/mozilla/mozilla_webhook_sync/blob/master/readme/heroku_scheduler.png?raw=true


**Django Settings files for Heroku**

It is located in::

    settings/prod.py

====================================
Nationbuilder Petition Signup Module
====================================

Webhooks
--------

This whole module is behind the scene, living in a Heroku instance. It is not meant to be seen by the public, and it is running automatically to sync the sign up information from Nationbuilder to Salesforce.

In Nationbuilder admin panel, under "Settings" -> "Developer" -> "Webhooks" There are two webhooks::

  Person created
  Person changed

that will POST the user information to the Django webhook module.

**Receiving POST data from Nationbuilder**

For Person created, there is a bug in Nationbuilder that is setting two to three POSTs to the webhook, only the one with user_language that is not null that should be use, we are ignoring the other POSTs as they will create duplicated information in Salesforce.

The webhook app is "**nb_hook**", and the main file is **views.py**. For receiving the POST data for creating new users (create_hook) and updating existing users (update_hook).

The view file's (**views.py**) purpose is to save the data in the internal database, they are saved into a Heroku database, check out ContactSync Model in models.py file.


Heroku Scheduler
----------------

The data saved in ContactSync table are not sync'ed into Salesforce yet. The sync is processed via a Heroku Scheduler command. The command for that is::

    python prod.py send_contacts_to_sf


Prod.py is the same as manage.py but with the setting path pointed **settings/prod.py**

This command will pull the data from the table, and send them to Salesforce. Currently there is a limit, pulling 500 posts each time.

There is an API count limit for using SalesForce, so there is a daily cap (set via Heroku "Config Vars" in "Settings"). Each insert/update user takes three API calls.

This is an example of the "insert user" action::

    def insert_user(object):
    sf = get_sf_session()

    # search for existing user
    query = "select Id from Contact where Email = '{0}'".format(object['Email'])
    add_count()
    results = sf.query_all(query)
    try:
        object_id = results['records'][0]['Id']
    except:
        object_id = None

    if object_id is not None:
        add_count()
        sf.Contact.update(object_id, object)
        return {'id': object_id}
    else:
        add_count()
        return sf.Contact.create(object)

You should notice that there are three add_count() function called in the insert_user action.

For the command script, please look up **nb_book/management/commands/send_contacts_to_sf.py**


Fields Synced to SalesForce
---------------------------

Currently, these are the user fields from Nationbuilder that are pushed to the webhook, and synced into Salesforce via Force API

*Contact*::

        'SALESFORCE FIELD NAME':     'NATIONBUILDER FIELD NAME'
        'FirstName':                 person['first_name'],
        'LastName':                  person['last_name'],
        'Email':                     person['email'],
        'MailingCountryCode':        country_code, (if OTHER is selected, it will NOT send anything to Salesforce
        'Subscriber__c':             person['email_opt_in'],
        'Sub_Mozilla_Foundation__c': person['email_opt_in'],
        'Email_Language__c':         person['user_language'],
        'RecordTypeId':              settings.ADVOCACY_RECORD_TYPE_ID  # advocacy record type (set in Heroku "config vars" field)
        'Signup_Source_URL__c':      'changecopyright.org',


*CampaignMember*::

Once a user is created / updated in Salesforce, Salesforce will send a signal back to the webhook, the webhook will then send another API POST to Salesforce, this time to CampaignMember module, in order to include the new user to the campaign. In this step, the following information is sent::

        'ContactId':                sf_contact_id['id'], (sf_contact_id from the result when user is created/updated)
        'CampaignId':               dj_sf_campaign_id, (created via Nationbuilder tag)
        'Campaign_Language__c':     person['user_language'],
        'Campaign_Email_Opt_In__c': person['email_opt_in'],

It will then update the "synced" column in ContactSync from *False* to *True*


Database Logs
-------------

For debugging purpose, we have a database table for storing all records. It includes all records from Nationbuilder in JSON format, email, sync type (create or update), and sync status (boolean)

It is in the "Log" model and the records are saved via "save_user" method in **nb_book/views.py**


===============================
Nationbuilder Event Sync Module
===============================

Custom Django Command
---------------------

Maker Event is using a different method to sync the data into Salesforce, as Nationbuilder does not provide webhook support for event creation or update. In order to sync we will have to do a pull from Nationbuilder API and send it to Salesforce manually. We are using a Heroku scheduler to run the sync command hourly.

The Maker Party app is "events", and the main sync command is in management/commands/sync_events_to_salesforce.py. The command should be::

    python prod.py sync_events_to_salesforce

Like the Contact sync above, each SalesForce api call will add toward the daily count limit.


Nationbuilder API -> sync module -> Salesforce API
--------------------------------------------------

The sync module will send request to Nationbuilder to get a full list of events, save it in the sync module for fast referencing, and send the events to Salesforce. If an event is identical from the previous sync, or has been sync'ed in less than 60 minutes, the sync module will skip it. Currently, the sync occurs hourly.

Fields synced to SalesForce
---------------------------

Here are the fields that are sync'ed into Salesforce:

*Campaign*::

            'Name': event['name'],
            'Type': 'Event',
            'Location__c': insert_address(event),
            'ParentId': settings.EVENT_PARENT_ID,
            'IsActive': True

*CampaignMember*::

            'ContactId': sf_contact_id['id'],
            'CampaignId': event_dj.sf_id,
            'Campaign_Language__c': user_details['person']['user_language'],
            'Campaign_Member_Type__c': "Attendee",
            'Campaign_Email_opt_in__c': user_details['person']['email_opt_in'],

*Contact*::

            'FirstName': user_details['person']['first_name'],
            'LastName': user_details['person']['last_name'],
            'Email': user_details['person']['email'],
            'MailingCountryCode': country_code,
            'Email_Language__c': user_language,
            'RecordTypeId': settings.ADVOCACY_RECORD_TYPE_ID_STG,  # advocacy record type
            'Subscriber__c': user_details['person']['email_opt_in'],
            'Sub_Maker_Party__c': user_details['person']['email_opt_in'],
            'Signup_Source_URL__c': 'makerparty.community',

