#-*- coding:utf8 -*-
import json
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade,ReplayPostTrade,WAIT_AUDIT_STATUS,WAIT_PREPARE_SEND_STATUS\
    ,WAIT_CHECK_BARCODE_STATUS,IN_EFFECT,WAIT_SELLER_SEND_GOODS
from shopback.monitor.models import POST_MODIFY_CODE,POST_SUB_TRADE_ERROR_CODE
from shopback.orders.models import REFUND_APPROVAL_STATUS
from auth import apis
import logging 

logger =  logging.getLogger('tradepost.handler')

__author__ = 'meixqhi'



class OrderInline(admin.TabularInline):
    
    model = MergeOrder
    fields = ('oid','outer_id','outer_sku_id','title','buyer_nick','price','payment','num','sku_properties_name',
                    'refund_id','refund_status','status','sys_status')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }


class MergeTradeAdmin(admin.ModelAdmin):
    list_display = ('id','tid','user','buyer_nick','type','payment','create_date','pay_date'
                    ,'status','logistics_company','is_picking_print','is_express_print','is_send_sms'
                    ,'has_memo','has_refund','sys_status','operator','reason_code')
    list_display_links = ('tid',)
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    ordering = ['pay_time',]
    list_per_page = 100
     
    def pay_date(self, obj):
        return obj.pay_time.strftime('%Y-%m-%d %H:%M')

    pay_date.short_description = '付款日期'.decode('utf8')
    pay_date.admin_order_field = 'pay_time'
    
    def create_date(self, obj):
        return obj.created.strftime('%Y-%m-%d %H:%M')
    
    create_date.short_description = '生成日期'.decode('utf8')
    create_date.admin_order_field = 'created'
    
    inlines = [OrderInline]
    
    list_filter   = ('sys_status','status','user','type')
    search_fields = ['buyer_nick','tid','reason_code']
    #--------设置页面布局----------------
    fieldsets =(('订单基本信息:', {
                    'classes': ('collapse',),
                    'fields': ('tid','user','seller_nick','buyer_nick','payment','total_num','discount_fee'
                               ,'adjust_fee','post_fee','total_fee','alipay_no','seller_cod_fee','buyer_cod_fee','cod_fee'
                               ,'cod_status','buyer_message','seller_memo','created','pay_time','modified','consign_time'
                               ,'type','status')
                }),
                ('收货人及物流信息:', {
                    'classes': ('collapse',),
                    'fields': ('shipping_type','out_sid','logistics_company','receiver_name','receiver_state'
                               ,'receiver_city','receiver_district','receiver_address','receiver_zip','receiver_mobile','receiver_phone')
                }),
                ('系统内部信息:', {
                    'classes': ('collapse',),
                    'fields': ('weight','post_cost','is_picking_print','is_express_print','is_send_sms','has_memo','has_refund','remind_time'
                               ,'sys_memo','refund_num','sys_status','reason_code')
                }))

     #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }
    
    #--------定义action----------------
    def check_order(self, request, queryset):
        queryset.filter(sys_status=WAIT_AUDIT_STATUS,reason_code='').exclude(logistics_company=None).update(sys_status=WAIT_PREPARE_SEND_STATUS)
        return queryset

    check_order.short_description = "审核订单".decode('utf8')
    
    def sync_trade_post_taobao(self, request, queryset):

        trade_ids = [t.id for t in queryset]
        prapare_trades = queryset.filter(is_picking_print=True,is_express_print=True,sys_status=WAIT_PREPARE_SEND_STATUS
                                         ,operator=request.user.username).exclude(out_sid='')
        if prapare_trades.count() == 0:
            return queryset 
        for trade in prapare_trades:
            if not trade.tid and trade.type == 'direct':
                MergeTrade.objects.filter(tid=trade.tid).update(sys_status=WAIT_CHECK_BARCODE_STATUS
                                                                ,consign_time=datetime.datetime.now())
                continue
            try:
                trade_modified = apis.taobao_trade_get(tid=trade.tid,fields='tid,modified',tb_user_id=trade.seller_id)
                latest_modified = trade_modified['trade_get_response']['trade']['modified']
                if latest_modified==trade.modified:
                    response = apis.taobao_logistics_online_send(tid=trade.tid,out_sid=trade.out_sid
                                                  ,company_code=trade.logistics_company.code,tb_user_id=trade.seller_id)  
                    if not response['delivery_confirm_send_response']['shipping']['is_success']:
                        raise Exception('订单(%d)淘宝发货失败'.decode('utf8')%trade.tid)
                else:
                    raise Exception('订单(%d)本地修改日期(%s)与线上修改日期(%s)不一致'.decode('utf8')%(trade.tid,trade.modified,latest_modified))
            except Exception,exc:
                trade.append_reason_code(POST_MODIFY_CODE)
                MergeTrade.objects.filter(tid=trade.tid).update(sys_status=WAIT_AUDIT_STATUS)
                logger.error(exc.message,exc_info=True)
            else:
                MergeTrade.objects.filter(tid=trade.tid).update(sys_status=WAIT_CHECK_BARCODE_STATUS,consign_time=datetime.datetime.now())
                
                merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.tid)
                for merge_buyer_trade in merge_buyer_trades:
                    sub_merge_trade = MergeTrade.objects.get(tid=merge_buyer_trade.sub_tid)
                    try:
                        trade_modified = apis.taobao_trade_get(tid=trade.tid,fields='tid,modified',tb_user_id=trade.seller_id)
                        latest_modified = trade_modified['trade_get_response']['trade']['modified']
                        if latest_modified==trade.modified:
                            response = apis.taobao_logistics_online_send(tid=merge_buyer_trade.sub_tid,out_sid=trade.out_sid
                                                          ,company_code=trade.logistics_company.code,tb_user_id=trade.seller_id)  
                            if not response['delivery_confirm_send_response']['shipping']['is_success']:
                                raise Exception('订单(%d)的子订单(%d)淘宝发货失败'.decode('utf8')%(trade.tid,merge_buyer_trade.sub_tid))
                        else:
                            raise Exception('订单(%d)的子订单(%d)本地修改日期(%s)与线上修改日期(%s)不一致'.decode('utf8')%
                                            (trade.tid,merge_buyer_trade.sub_tid,trade.modified,latest_modified))
                    except Exception,exc:
                        trade.append_reason_code(POST_SUB_TRADE_ERROR_CODE)
                        MergeTrade.objects.filter(tid=merge_buyer_trade.sub_tid).update(sys_status=WAIT_AUDIT_STATUS)
                        logger.error(exc.message,exc_info=True)
                    else:
                        MergeTrade.objects.filter(tid=sub_merge_trade.tid).update(sys_status=WAIT_CHECK_BARCODE_STATUS,consign_time=datetime.datetime.now())
#        MergeTrade.objects.filter(tid__in=(queryset[0].tid,queryset[1].tid)).update(sys_status=WAIT_AUDIT_STATUS,is_picking_print=True,is_express_print=True)
#        MergeTrade.objects.filter(tid__in=[s.tid for s in queryset]).update(sys_status=WAIT_CHECK_BARCODE_STATUS,is_picking_print=True,is_express_print=True)
   
        queryset = MergeTrade.objects.filter(id__in=trade_ids)
        post_trades = queryset.filter(sys_status=WAIT_CHECK_BARCODE_STATUS)
        trade_items = {}
        for trade in post_trades:
            used_orders = trade.merge_trade_orders.filter(status=WAIT_SELLER_SEND_GOODS,sys_status=IN_EFFECT)\
                .exclude(refund_status__in=REFUND_APPROVAL_STATUS)
            for order in used_orders:
                outer_id = order.outer_id or str(order.num_iid)
                outer_sku_id = order.outer_sku_id or str(order.sku_id)
                
                if trade_items.has_key(outer_id):
                    
                    trade_items[outer_id]['num'] += order.num
                    skus = trade_items[outer_id]['skus']
                    if skus.has_key(outer_sku_id):
                        skus[outer_sku_id]['num'] += order.num
                    else:
                        skus[outer_sku_id] = {'sku_name':order.sku_properties_name,'num':order.num}
                else:
                    trade_items[outer_id]={
                                           'num':order.num,
                                           'title':order.title,
                                           'skus':{outer_sku_id:{'sku_name':order.sku_properties_name,'num':order.num}}
                                           }
                     
        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.seller_nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['pay_time'] = trade.pay_time.strftime('%Y-%m-%d %H:%M:%S')
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)
            
        trade_list = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
        for trade in trade_list:
            skus = trade[1]['skus']
            trade[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['num'],reverse=True)
 
        response_dict = {'trades':trades,'trade_items':trade_list}
        
        try:
            ReplayPostTrade.objects.create(operator=request.user.username,post_data=json.dumps(response_dict))
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            
        return render_to_response('trades/tradepostsuccess.html',response_dict,
                                  context_instance=RequestContext(request),mimetype="text/html")
                          
    sync_trade_post_taobao.short_description = "同步发货".decode('utf8')
    
    actions = ['check_order','sync_trade_post_taobao']
    
    


admin.site.register(MergeTrade,MergeTradeAdmin)


class MergeOrderAdmin(admin.ModelAdmin):
    list_display = ('id','tid','oid','seller_nick','buyer_nick','price','num_iid','sku_id','num','outer_sku_id','sku_properties_name',
                    'payment','refund_id','refund_status','outer_id','cid','status')
    list_display_links = ('oid','tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    list_filter = ('seller_nick','status','refund_status')
    search_fields = ['oid','tid','buyer_nick','num_iid','sku_properties_name']


admin.site.register(MergeOrder,MergeOrderAdmin)


class MergeBuyerTradeAdmin(admin.ModelAdmin):
    list_display = ('sub_tid','main_tid','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']

    search_fields = ['sub_tid','main_tid']
    

admin.site.register(MergeBuyerTrade,MergeBuyerTradeAdmin)


class ReplayPostTradeAdmin(admin.ModelAdmin):
    list_display = ('id','operator','post_data','created')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    #ordering = ['created_at']
    search_fields = ['operator','id']
    
    def replay_post(self, request, queryset):
        object = queryset.order_by('-created')[0]
        replay_data = json.loads(object.post_data)
        return render_to_response('trades/tradepostsuccess.html',replay_data,
                                  context_instance=RequestContext(request),mimetype="text/html")
    
    replay_post.short_description = "重现发货清单".decode('utf8')
    
    actions = ['replay_post']

admin.site.register(ReplayPostTrade,ReplayPostTradeAdmin)
