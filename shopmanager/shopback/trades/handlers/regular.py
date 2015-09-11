#-*- coding:utf8 -*-
import os
import datetime
from django.conf import settings
from django.db.models import Q

from .handler import BaseHandler
from shopback import paramconfig as pcfg
from shopback.base import log_action,User, ADDITION, CHANGE
from shopback.items.models import Product
from common.modelutils import  update_model_fields

MAX_YOUNI_CAT = 3

class RegularSaleHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        
        if (not kwargs.get('first_pay_load',None) or 
            merge_trade.type not in (pcfg.WX_TYPE,pcfg.SALE_TYPE)):
            return False
        #秒杀订单 取消定时
        if (merge_trade.user.visitor_id.lower().endswith('miaosha') 
            or merge_trade.user.nick.find(u'秒杀') >= 0):
            return False
        
        orders = merge_trade.inuse_orders.extra(where=["CHAR_LENGTH(outer_id)>=9"])\
            .filter(Q(outer_id__startswith="9")|Q(outer_id__startswith="1")|Q(outer_id__startswith="8"))
        
        return  orders.count() > 0
                
            
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG REGULARSALE:',merge_trade
        
        if merge_trade.sys_status == pcfg.ON_THE_FLY_STATUS:
            return 
        
        for order in merge_trade.normal_orders:
            try:
                product = Product.objects.get(outer_id=order.outer_id)
                if product.category__cid <= MAX_YOUNI_CAT:
                    return
            except Product.DoesNotExist: 
                continue
            
        remind_time = datetime.datetime.now() + datetime.timedelta(days=settings.REGULAR_DAYS)
        merge_trade.sys_status = pcfg.REGULAR_REMAIN_STATUS
        
        merge_trade.remind_time = remind_time
        merge_trade.sys_memo += u'特卖订单，到货再发'
        
        update_model_fields(merge_trade,update_fields=['sys_memo','remind_time','sys_status'])
        
        log_action(merge_trade.user.user.id,merge_trade,CHANGE, u'定时(%s)提醒'%remind_time)
        
        