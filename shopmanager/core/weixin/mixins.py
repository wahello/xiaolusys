# coding:utf-8
import re
import json
import urllib
from django.conf import settings

from . import options 

OPENID_RE = re.compile('^[a-zA-Z0-9-_]{28}$')


class WeixinAuthMixin(object):
    
    _wxpubid = settings.WEIXIN_APPID
    _wxpubsecret = settings.WEIXIN_SECRET
    
    def is_from_weixin(self, request):
        if hasattr(self, '_isfromweixin'):
            return self._isfromweixin
        agent = request.META.get('HTTP_USER_AGENT', None)
        self._isfromweixin = "MicroMessenger" in agent
        return self._isfromweixin
    
    def set_appid_and_secret(self,appid,appsecret):
        self._wxpubid = appid
        self._wxpubsecret = appsecret
        
    def valid_openid(self, openid):
        if not openid:
            return False
        if not OPENID_RE.match(openid):
            return False
        return True
    
    def get_openid_and_unionid(self, request):
        code    = request.GET.get('code')
        return options.get_user_unionid(
            code,
            appid=self._wxpubid,
            secret=self._wxpubsecret,
            request=request
        )
    
    def get_wxauth_redirct_url(self,request,scope="snsapi_base"):
        """ 微信网页基本授权 """
        absolute_url = request.build_absolute_uri().split('#')[0]
        absolute_url = re.sub('&?(code|state)=[\w]+','',absolute_url)
        params = dict([('appid',self._wxpubid),
                      ('redirect_uri',absolute_url),
                      ('response_type','code'),
                      ('scope',scope),
                      ('state','135')])
        return options.gen_weixin_redirect_url(params)
    
    def get_snsuserinfo_redirct_url(self,request):
        """ 微信网页高级授权 """
        return self.get_wxauth_redirct_url(request,scope="snsapi_userinfo")
    
    