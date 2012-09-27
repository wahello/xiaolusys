import os.path
import posixpath

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
#
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#        'NAME': os.path.join(PROJECT_ROOT, 'database.db'),                      # Or path to database file if using sqlite3.
#        'USER': '',                      # Not used with sqlite3.
#        'PASSWORD': '',                  # Not used with sqlite3.
#        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shoptest2',                      # Or path to database file if using sqlite3.
        'USER': 'meixqhi',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'chartit',
    'south',
    'gunicorn',
    'raven.contrib.django',
    'djangorestframework',
    'djcelery',
    'djkombu',
    'deamon',
    'deamon.celery_sentry',

    'shopback.users',
    'shopback.items',
    'shopback.amounts',
    'shopback.categorys',
    'shopback.fenxiao',
    'shopback.logistics',
    'shopback.monitor',
    'shopback.orders',
    'shopback.trades',
    'shopback.refunds',
    'shopback.suppliers',
    'shopback.purchases',

    'shopapp.autolist',
    'shopapp.collector',
    'shopapp.memorule',
    'shopapp.report',
    'shopapp.syncnum',
    'shopapp.asynctask',

    #'devserver',
    'django.contrib.admin',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

if DEBUG:
    STATICFILES_DIRS = (
       os.path.join(PROJECT_ROOT,'site_media',"static"),
    )
else :
    STATIC_ROOT = os.path.join(PROJECT_ROOT,'site_media', "static")

RAVEN_CONFIG = {
    'dsn': 'http://981b39c5e0c14275b7da7c671eb76513:faf7926e18a5403f8e054996042ad592@sentry/2',
    'register_signals': True,
}

#SENTRY_CLIENT = 'raven.contrib.django.DjangoClient'

SITE_URL = 'http://127.0.0.1:8000/'

#from raven.contrib.django.models import client
#
#client.captureException()
 

APPKEY = '21189152'  #app name huyi ERP test1 ,meixqhi
APPSECRET = '5250e0e553fb65f674752d5850af547c'

#APPKEY = '12686908'  #app name super ERP ,younishijie
#APPSECRET = 'b3ddef5982a23c636739289949c01f59'

#APPKEY = '21165266'  #app name huyi ERP ,younishijie
#APPSECRET  = 'ea5f5687a856ec58199d538cfa04496d'

AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = ''.join([SITE_URL,'accounts/login/auth/'])
TAOBAO_API_ENDPOINT = 'https://eco.taobao.com/router/rest'

SCOPE = 'item,promotion,usergrade'

REFRESH_URL = 'https://oauth.taobao.com/token'

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerifCondensed-BoldItalic.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT,'site_media',"asyncfile")


DEVSERVER_MODULES = (
    'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    #'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    'devserver.modules.ajax.AjaxDumpModule',
    'devserver.modules.profile.MemoryUseModule',
    'devserver.modules.cache.CacheSummaryModule',
    #'devserver.modules.profile.LineProfilerModule',
)

