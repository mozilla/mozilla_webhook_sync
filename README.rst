Set up
---------------------


Set up local settings file
---------------------
Clone settings/local-dist and rename it to settings/local.py


Virtual Env
---------------------
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


Nationbuilder Webhooks -- User fields
---------------------
The whole module is behind the scene, living in an Heroku instance. It is not meant to be seen by the public, and it is running automatically to sync the sign up information from Nationbuilder to Salesforce.

In Nationbuilder admin panel, under "Settings" -> "Developer" -> "Webhooks" There are two webhooks::

  Person created
  Person changed

that will POST the user information to the Django webhook module.

For Person created, there is a bug in Nationbuilder that is setting two to three POSTs to the webhook, only the one with user_language that is not null that should be use, we are ignoring the other POSTs as they will create duplicated information in Salesforce.

Currently, these are the user fields from Nationbuilder that are pushed to the webhook, and synced into Salesforce via Force API::

        'SALESFORCE FIELD NAME':     'NATIONBUILDER FIELD NAME'
        'FirstName':                 person['first_name'],
        'LastName':                  person['last_name'],
        'Email':                     person['email'],
        'MailingCountryCode':        country_code, (if OTHER is selected, it will NOT send anything to Salesforce
        'Subscriber__c':             person['email_opt_in'],
        'Sub_Mozilla_Foundation__c': person['email_opt_in'],
        'Email_Language__c':         person['user_language'],
        'RecordTypeId':              settings.ADVOCACY_RECORD_TYPE_ID  # advocacy record type (set in Heroku "config vars" field)


Nationbuilder Webhooks -- CampaignMember fields
---------------------
Once a user is created / updated in Salesforce, Salesforce will send a signal back to the webhook, the webhook will then send another API POST to Salesforce, this time to CampaignMember module, in order to include the new user to the campaign. In this step, the following information is sent::

        'ContactId':                sf_contact_id['id'], (sf_contact_id from the result when user is created/updated)
        'CampaignId':               dj_sf_campaign_id, (created via Nationbuilder tag)
        'Campaign_Language__c':     person['user_language'],
        'Campaign_Email_Opt_In__c': person['email_opt_in'],


Nationbuilder Webhooks -- Salesforce API
---------------------
The sync will utilize three api count each time an user is created: 1) check if user exists; 2) create/update user 3) add CampaignMember linkage. So if there are 100 signups, the webhook will be using 300 API counts.


Nationbuilder Webhooks -- Database Log
---------------------
For debugging purpose, we have a database table for storing all records. It includes all records from Nationbuilder in JSON format, email, sync type (create or update), and sync status (boolean)


Nationbuilder Webhooks -- Update User
_____________________
The update user protocol utilizes database table. The data is stored in a local database, via /update, and in Heroku it is using the Scheduler to sync the updated users to Salesforce in batches, via /save_update. Once it is updated, it will check the "synced" field from False to True.