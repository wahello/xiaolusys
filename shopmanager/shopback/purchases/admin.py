#-*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback import paramconfig as pcfg
from shopback.items.models import Product,ProductSku
from shopback.purchases.models import Purchase,PurchaseItem,\
    PurchaseStorage,PurchaseStorageItem,PurchasePaymentItem,PurchaseStorageRelationship
from shopback.purchases import permissions as perms

import logging 

logger =  logging.getLogger('purchases.handler')

class PurchaseItemInline(admin.TabularInline):
    
    model = PurchaseItem
    fields = ('outer_id','name','outer_sku_id','properties_name','purchase_num','storage_num'
              ,'price','total_fee','payment','arrival_status','status','extra_info')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})}
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not perms.has_check_purchase_permission(request.user):
            return self.readonly_fields + self.fields[0:-1] 
        return self.readonly_fields
    

class PurchaseStorageItemInline(admin.TabularInline):
    
    model = PurchaseStorageItem
    fields = ('outer_id','name','outer_sku_id','properties_name','storage_num','status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not perms.has_confirm_storage_permission(request.user):
            print self.fields
            return self.fields
        return self.readonly_fields


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_title_link','origin_no','supplier','deposite','purchase_type',
                    'receiver_name','total_fee','payment','forecast_date',
                    'post_date','service_date','arrival_status','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','arrival_status','supplier','deposite','purchase_type')
    search_fields = ['id','origin_no','extra_name']
    
    def purchase_title_link(self, obj):
        symbol_link = obj.extra_name or u'【空标题】'

        return '<a href="/purchases/%d/" >%s</a>'%(obj.id,symbol_link) 
    
    purchase_title_link.allow_tags = True
    purchase_title_link.short_description = "标题"
    
    inlines = [PurchaseItemInline]

    #--------设置页面布局----------------
    fieldsets =(('采购单信息:', {
                    'classes': ('expand',),
                    'fields': (('supplier','deposite','purchase_type')
                               ,('origin_no','extra_name','total_fee','payment')
                               ,('forecast_date','service_date','post_date')
                               ,('arrival_status','status','extra_info'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not perms.has_check_purchase_permission(request.user):
            return self.readonly_fields+('arrival_status','total_fee','payment','status',)
        return self.readonly_fields

admin.site.register(Purchase,PurchaseAdmin)


class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase','outer_id','name','outer_sku_id','properties_name','purchase_num','price'
                    ,'total_fee','payment','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']

admin.site.register(PurchaseItem,PurchaseItemAdmin)


class PurchaseStorageAdmin(admin.ModelAdmin):
    list_display = ('id','storage_name_link','origin_no','supplier','deposite','storage_num','total_fee','payment','post_date','created','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status','supplier','deposite')
    search_fields = ['id','out_sid','extra_name','origin_no']
    
    def storage_name_link(self, obj):
        symbol_link = obj.extra_name or u'【空标题】'

        return '<a href="/purchases/storage/%d/" >%s</a>'%(obj.id,symbol_link) 
    
    storage_name_link.allow_tags = True
    storage_name_link.short_description = "标题"
    
    inlines = [PurchaseStorageItemInline]
    
    #--------设置页面布局----------------
    fieldsets =(('采购入库单信息:', {
                    'classes': ('expand',),
                    'fields': (('origin_no','supplier','deposite')
                               ,('forecast_date','post_date','logistic_company','out_sid')
                               ,('storage_num','total_fee','payment')
                               ,('extra_name','status','extra_info'))
                }),)
    
    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'16'})},
        models.FloatField: {'widget': TextInput(attrs={'size':'8'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    def get_readonly_fields(self, request, obj=None):
        if not perms.has_confirm_storage_permission(request.user):
            return self.readonly_fields+('arrival_status','storage_num','total_fee','payment','status',)
        return self.readonly_fields

admin.site.register(PurchaseStorage,PurchaseStorageAdmin)


class PurchaseStorageItemAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_storage','supplier_item_id','outer_id','name','outer_sku_id',
                    'properties_name','storage_num','created','modified','status')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    
admin.site.register(PurchaseStorageItem,PurchaseStorageItemAdmin)


class PurchaseStorageRelationshipAdmin(admin.ModelAdmin):
    list_display = ('id','purchase_id','purchase_item_id','storage_id','storage_item_id',
                    'outer_id','outer_sku_id','is_addon','storage_num','total_fee','payment')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('is_addon',)
    search_fields = ['purchase_id','purchase_item_id','storage_id','outer_id']
    

admin.site.register(PurchaseStorageRelationship,PurchaseStorageRelationshipAdmin)


class PurchasePaymentItemAdmin(admin.ModelAdmin):
    list_display = ('id','pay_type','payment','purchase','storage','pay_time','status','extra_info')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status',)
    search_fields = ['id']
    

admin.site.register(PurchasePaymentItem,PurchasePaymentItemAdmin)


