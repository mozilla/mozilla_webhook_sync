from base import *
import dj_database_url


WSGI_APPLICATION = 'gettingstarted.wsgi.application'

# Update database configuration with $DATABASE_URL.
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)
DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}

DEBUG = False