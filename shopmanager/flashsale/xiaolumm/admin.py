#-*- coding:utf8 -*-
from django.contrib import admin
from flashsale.xiaolumm.models import UserGroup

from shopback.base.options import DateFieldListFilter
from .models import Clicks,XiaoluMama,AgencyLevel,CashOut,CarryLog

from django import forms

class XiaoluMamaForm( forms.ModelForm ):
    
    def __init__(self, *args, **kwargs):
        super(XiaoluMamaForm, self).__init__(*args, **kwargs)
        self.initial['cash']    = self.instance.get_cash_display()
        self.initial['pending'] = self.instance.get_pending_display()
    
    cash    = forms.FloatField(label=u'可用现金',min_value=0)
    pending = forms.FloatField(label=u'可用现金',min_value=0)
    
    class Meta:
        model = XiaoluMama
    
    def  clean_cash(self):
        cash = self.cleaned_data['cash']
        return int(cash * 100)
    
    def  clean_pending(self):
        pending = self.cleaned_data['pending']
        return int(pending * 100)
    

class XiaoluMamaAdmin(admin.ModelAdmin):
    
    user_groups = []
    
    form = XiaoluMamaForm
    list_display = ('id','mobile','province','weikefu','agencylevel','charge_link','group_select','created','status')
    list_filter = ('agencylevel','manager','status','charge_status',('created',DateFieldListFilter),'user_group')
    search_fields = ['id','mobile','manager','weikefu']
    
    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        default_code = ['BLACK','NORMAL']
        default_code.append(request.user.username)
        
        self.user_groups = UserGroup.objects.filter(code__in=default_code)

        return super(XiaoluMamaAdmin,self).get_changelist(request,**kwargs)
    
    def group_select(self, obj):

        categorys = set(self.user_groups)

        if obj.user_group:
            categorys.add(obj.user_group)

        cat_list = ["<select class='group_select' gid='%s'>"%obj.id]
        cat_list.append("<option value=''>-------------------</option>")
        for cat in categorys:

            if obj and obj.user_group == cat:
                cat_list.append("<option value='%s' selected>%s</option>"%(cat.id,cat))
                continue

            cat_list.append("<option value='%s'>%s</option>"%(cat.id,cat))
        cat_list.append("</select>")

        return "".join(cat_list)
    
    group_select.allow_tags = True
    group_select.short_description = u"所属群组"
    
    def charge_link(self, obj):

        if obj.charge_status == XiaoluMama.CHARGED:
            return u'[ %s ]' % obj.manager_name
        
        if obj.charge_status == XiaoluMama.FROZEN:
            return obj.get_charge_status_display()

        return ('<a href="javascript:void(0);" class="btn btn-primary btn-charge" '
                + 'style="color:white;" sid="{0}">接管</a></p>'.format(obj.id))
        
    charge_link.allow_tags = True
    charge_link.short_description = u"接管信息"
    
    
    class Media:
        css = {"all": ("admin/css/forms.css","css/admin/dialog.css"
                       ,"css/admin/common.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("js/admin/adminpopup.js","js/xlmm_change_list.js")
    
    
admin.site.register(XiaoluMama, XiaoluMamaAdmin) 
    

class AgencyLevelAdmin(admin.ModelAdmin):
    list_display = ('category','deposit','cash','basic_rate','target','extra_rate','created')
    search_fields = ['category']
    
admin.site.register(AgencyLevel, AgencyLevelAdmin) 


class ClicksAdmin(admin.ModelAdmin):
    list_display = ('linkid','openid','created')
    list_filter = ('linkid',)
    search_fields = ['openid',]

admin.site.register(Clicks, ClicksAdmin) 


class CashOutAdmin(admin.ModelAdmin):
    list_display = ('xlmm','value','status','created')
    list_filter  = ('status',)
    search_fields = ['xlmm']
    
admin.site.register(CashOut, CashOutAdmin) 


class CarryLogAdmin(admin.ModelAdmin):
    list_display = ('xlmm', 'buyer_nick', 'value', 'status', 'created')
    list_filter = ('status',)
    search_fields = ['xlmm', 'buyer_nick']

admin.site.register(CarryLog, CarryLogAdmin)
