__author__ = 'zfz'

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SESSION_EXPIRE_AT_BROWSER_CLOSE = False  
SESSION_COOKIE_AGE = 12 * 60 * 60             

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',  # Or path to database file if using sqlite3.
        'USER': 'meixqhi',  # Not used with sqlite3.
        'PASSWORD': '123123',  # Not used with sqlite3.
        'HOST': '192.168.1.101',  # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS':  {'init_command': 'SET storage_engine=Innodb;',
                     'charset': 'utf8'},  # storage_engine need mysql>5.4,and table_type need mysql<5.4
    }
}


if DEBUG:
    STATICFILES_DIRS = (
       os.path.join(PROJECT_ROOT, "site_media", "static"),
    )
    STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "local")
else:
    STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")
    
M_STATIC_URL = '/static/wap/'

MIDDLEWARE_CLASSES = (
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'middleware.middleware.SecureRequiredMiddleware',
    'middleware.middleware.DisableDRFCSRFCheck',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if DEBUG:
    MIDDLEWARE_CLASSES = ('middleware.middleware.ProfileMiddleware',
                          'middleware.middleware.QueryCountDebugMiddleware',) + MIDDLEWARE_CLASSES


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
    
RAVEN_CONFIG = {
    'dsn': 'http://ada7dc70824c43fd8ba430db3827cd62:283aaec97585411ca9e66bb8bb1a9c63@sentry.huyi.so:8089/3',
    'register_signals': True,
}

#################### change this site to yourself test domain #######################
SITE_URL = 'http://192.168.1.11:9000/' 
M_SITE_URL = 'http://192.168.1.11:9000' 

####################### TRADE HANDLERS CONFIG ########################
TRADE_HANDLERS_PATH = (
   'shopback.trades.handlers.InitHandler',
   'shopback.trades.handlers.ConfirmHandler',
   'shopback.trades.handlers.SplitHandler',
   'shopback.trades.handlers.MemoHandler',
   'shopback.trades.handlers.DefectHandler',
   'shopback.trades.handlers.RuleMatchHandler',
   'shopback.trades.handlers.StockOutHandler',
   'shopback.trades.handlers.MergeHandler',
   'shopback.trades.handlers.RefundHandler',
   'shopback.trades.handlers.LogisticsHandler',
   'shopback.trades.handlers.InterceptHandler',
   'shopback.trades.handlers.FinalHandler',
)


#################### TAOBAO SETTINGS ###################
# APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
# APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

APPKEY = '1012545735'  # app name guanyi erp ,younishijie
APPSECRET = 'sandbox4a7f3927e06af6931eefb37f3'

TAOBAO_API_HOSTNAME = 'gw.api.tbsandbox.com'
AUTHRIZE_URL = 'https://oauth.tbsandbox.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.tbsandbox.com/token'
REDIRECT_URI = '/accounts/login/auth/'
TAOBAO_API_ENDPOINT = 'https://%s/router/rest' % TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL = 'http://stream.api.taobao.com/stream'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'


FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT, "site_media", "asyncfile")

################### HTTPS/SSL SETTINGS ##################

HTTPS_SUPPORT = False
SECURE_REQUIRED_PATHS = (
    '/admin/',
)

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_USE_CACHE':'default',
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 0,
    'DEFAULT_CACHE_KEY_FUNC':'rest_framework_extensions.utils.default_cache_key_func'
}
################### SALEORDER CONFIG ##################
#sale order regular days
REGULAR_DAYS = 20

################### WEIXIN SETTINGS ##################
#for weixin pub younishijie
WEIXIN_API_HOST = "https://api.weixin.qq.com"
WEIXIN_MEDIA_HOST = "http://file.api.weixin.qq.com"
WEIXIN_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
WEIXIN_QRCODE_HOST = "https://mp.weixin.qq.com"
WEIXIN_APPID  = 'wx91b20565c83072f6'
WEIXIN_SECRET = '38e6b5f94c0f4966460913b5c11284a9'
#for weixin pub xiaolumm,just for pay
WXPAY_APPID    = "wx3f91056a2928ad2d"
WXPAY_SECRET   = "e8e1f648a5e02492e1584e5413cef158"
#for weixin app
WXAPP_ID       = "wx25fcb32689872499"
WXAPP_SECRET   = "3c7b4e3eb5ae4cmeixqhisok060a872ee"

################### JINGDONG SETTINGS #################

JD_APP_KEY = 'FD41E99D04BF7EB6DECDA7043A4D57E1'
JD_APP_SECRET = 'e33d1f1b4abb4036b742787211624fe1'

JD_API_HOSTNAME = 'gw.api.360buy.com'
JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
JD_REDIRECT_URI = '/app/jd/login/auth/'
JD_API_ENDPOINT = 'http://%s/routerjson' % JD_API_HOSTNAME

################### PING++ SETTINGS ##################

PINGPP_APPID           = "app_qPCaj95Serj5PKOq"
PINGPP_APPKEY          = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT" #TEST KEY
PINGPP_CLENTIP         = "127.0.0.1"

################### Ntalker SETTINGS ##################

NTALKER_NOTIFY_URL = 'http://wx.ntalker.com/agent/weixin'
WX_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'
WX_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/media/upload'
WX_MEDIA_GET_URL = 'https://api.weixin.qq.com/cgi-bin/media/get'

################### QINIU SETTINGS ##################

QINIU_ACCESS_KEY = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
QINIU_SECRET_KEY = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"

LOGGER_HANDLERS = [
    'models',
    'queryset',
    'django.request',
    'sentry.errors',
    'celery.handler',
    'notifyserver.handler',
    'yunda.handler',
    'mail.handler',
    'xhtml2pdf',
    'restapi.errors',
    'weixin.proxy',
]

LOGGER_TEMPLATE = {
    'handlers': ['sentry','console'],
    'level': 'DEBUG',
    'propagate': True,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django-debug.log',
            'formatter': 'simple'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'INFO',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': dict([(handler,LOGGER_TEMPLATE) for handler in LOGGER_HANDLERS]),
}
