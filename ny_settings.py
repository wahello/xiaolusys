__author__ = 'zfz'

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
STATICFILES_DIRS = ()
STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media","static")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'tbshop',                      # Or path to database file if using sqlite3.
        'USER': 'meixqhi',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

#SITE_URL = "http://autolist.huyi.so/" 
SITE_URL = 'http://192.168.1.101/' 

#
#APPKEY = '21165266'  #app name huyi ERP ,younishijie
#APPSECRET  = 'ea5f5687a856ec58199d538cfa04496d'

APPKEY = '12686908'   #app name super ERP ,younishijie
APPSECRET = 'b3ddef5982a23c636739289949c01f59'

AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = ''.join([SITE_URL,'accounts/login/taobao/'])
TAOBAO_API_ENDPOINT = 'https://eco.taobao.com/router/rest'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = '/home/user1/deploy/taobao/site_media/asyncfile'
