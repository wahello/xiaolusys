#-*- coding:utf8 -*-
import time
import datetime
import calendar
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Q
from shopback import paramconfig as pcfg
from shopback.orders.models import Trade,Order
from shopback.trades.service import TradeService
from shopback.items.models import Product,ProductSku
from shopback.trades.models import MergeTrade,MergeBuyerTrade,ReplayPostTrade
from shopback.base import log_action,User as DjangoUser, ADDITION, CHANGE
from shopback.users.models import User,Customer
from auth import apis
import logging

logger = logging.getLogger('django.request')


class SubTradePostException(Exception):

    def __init__(self,msg=''):
        self.message  = msg

    def __str__(self):
        return self.message
     
def get_trade_pickle_list_data(post_trades):
    """生成配货单数据列表"""
    
    trade_items = {}
    for trade in post_trades:
        used_orders = trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT)\
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
        for order in used_orders:
            outer_id = order.outer_id or str(order.num_iid)
            outer_sku_id = order.outer_sku_id or str(order.sku_id)
            
            prod = None
            prod_sku = None
            try:
                prod = Product.objects.get(outer_id=outer_id)
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product=prod)
            except:
                pass
            
            location = prod_sku and prod_sku.get_districts_code() or (prod and prod.get_districts_code() or '')
            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order.num
                skus = trade_items[outer_id]['skus']
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order.num
                else:
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    skus[outer_sku_id] = {'sku_name':prod_sku_name,
                                          'num':order.num,
                                          'location':location}
            else:
                prod_sku_name = prod_sku.properties_name if prod_sku else order.sku_properties_name
                    
                trade_items[outer_id]={
                   'num':order.num,
                   'title': prod.name if prod else order.title,
                   'location':prod and prod.get_districts_code() or '',
                   'skus':{outer_sku_id:{
                        'sku_name':prod_sku_name,
                        'num':order.num,
                        'location':location}}
                }

    trade_list = sorted(trade_items.items(),key=lambda d:d[1]['num'],reverse=True)
    for trade in trade_list:
        skus = trade[1]['skus']
        trade[1]['skus'] = sorted(skus.items(),key=lambda d:d[1]['num'],reverse=True)
    
    return trade_list
     
def get_replay_results(replay_trade):
    
    reponse_result = replay_trade.post_data 
    if not reponse_result:

        trade_ids = replay_trade.trade_ids.split(',')
        queryset = MergeTrade.objects.filter(id__in=trade_ids)

        post_trades = queryset.filter(sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                     pcfg.WAIT_SCAN_WEIGHT_STATUS,pcfg.FINISHED_STATUS))
        trade_list = get_trade_pickle_list_data(post_trades)
        
        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.user.nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['company_name'] = (trade.logistics_company and 
                                          trade.logistics_company.name or '--')
            trade_dict['out_sid']    = trade.out_sid
            trade_dict['is_success'] = trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                            pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                            pcfg.FINISHED_STATUS)
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)
        
        reponse_result = {'trades':trades,'trade_items':trade_list,'post_no':replay_trade.id}
        
        replay_trade.succ_ids  = ','.join([str(t.id) for t in post_trades])
        replay_trade.succ_num  = post_trades.count()
        replay_trade.post_data = json.dumps(reponse_result)
        replay_trade.status    = pcfg.RP_WAIT_ACCEPT_STATUS
        replay_trade.finished  = datetime.datetime.now()
        replay_trade.save()
    else:
        reponse_result = json.loads(reponse_result)
    return reponse_result

@task()  
def sendTradeCallBack(trade_ids,*args,**kwargs):
    try: 
        replay_trade = ReplayPostTrade.objects.get(id=args[0])
    except:
        return None
    else:
        try:
            get_replay_results(replay_trade)
        except Exception,exc:
            logger.error('trade post callback error:%s'%exc.message,exc_info=True)
        return None
        
        
@task()
def sendTaobaoTradeTask(request_user_id,trade_id):
    """ 淘宝发货任务 """

    try:
        trade = MergeTrade.objects.get(id=trade_id)
        if  (not trade.is_picking_print or 
            not trade.is_express_print or not trade.out_sid 
            or trade.sys_status != pcfg.WAIT_PREPARE_SEND_STATUS):
            return trade_id
        
        if trade.status == pcfg.WAIT_BUYER_CONFIRM_GOODS:
            trade.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
            trade.consign_time = datetime.datetime.now()
            trade.save()
            return trade_id
        
        if trade.status != pcfg.WAIT_SELLER_SEND_GOODS or trade.reason_code  :
            trade.sys_status = pcfg.WAIT_AUDIT_STATUS
            trade.is_picking_print=False
            trade.is_express_print=False
            trade.save()
            log_action(request_user_id,trade,CHANGE,u'订单不满足发货条件')
            return trade_id
        
        if trade.type in (pcfg.DIRECT_TYPE,pcfg.EXCHANGE_TYPE,pcfg.REISSUE_TYPE):
            trade.sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS
            trade.status=pcfg.WAIT_BUYER_CONFIRM_GOODS
            trade.consign_time=datetime.datetime.now()
            trade.save()
            return trade_id
        
        company_name = trade.logistics_company.name
        out_sid   = trade.out_sid
    
        try:
            merge_buyer_trades = []
            #判断是否有合单子订单
            if trade.has_merge:
                merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.id)
        
            for sub_buyer_trade in merge_buyer_trades:
                
                try:
                    sub_trade = MergeTrade.objects.get(id=sub_buyer_trade.sub_tid)
                    sub_trade.out_sid           = trade.out_sid
                    sub_trade.logistics_company = trade.logistics_company
                    sub_trade.save()
                    if sub_trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                        TradeService(sub_trade.user.visitor_id,sub_trade).sendTrade()
                        
                except Exception,exc:
                    
                    sub_trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
                    sub_trade.sys_status=pcfg.WAIT_AUDIT_STATUS
                    sub_trade.is_picking_print=False
                    sub_trade.is_express_print=False
                    sub_trade.save()
                    log_action(request_user_id,sub_trade,CHANGE,
                               u'订单发货失败：%s'%exc.message)
                    raise SubTradePostException(exc.message)
                else:
                    
                    sub_trade.operator=trade.operator
                    sub_trade.sys_status=pcfg.FINISHED_STATUS
                    sub_trade.consign_time=datetime.datetime.now()
                    sub_trade.save()
                    log_action(request_user_id,sub_trade,CHANGE,
                               u'订单发货成功[%s:%s]'%(company_name,out_sid))
                        
            TradeService(trade.user.visitor_id,trade).sendTrade()
        
        except SubTradePostException,exc:
            trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
            trade.sys_status=pcfg.WAIT_AUDIT_STATUS
            trade.save()
            log_action(request_user_id,trade,CHANGE,
                       u'子订单(%d)发货失败:%s'%(sub_trade.id,exc.message))
            MergeTrade.objects.mergeRemover(trade)
        except Exception,exc:
            trade.append_reason_code(pcfg.POST_MODIFY_CODE)
            trade.sys_status=pcfg.WAIT_AUDIT_STATUS
            trade.is_picking_print=False
            trade.is_express_print=False
            trade.save()                                                                                       
            log_action(request_user_id,trade,CHANGE,
                       u'订单发货失败:%s'%exc.message)
            MergeTrade.objects.mergeRemover(trade) 
            
        else:
            trade.sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS
            trade.status=pcfg.WAIT_BUYER_CONFIRM_GOODS
            trade.consign_time=datetime.datetime.now()
            trade.save()
            log_action(request_user_id,trade,CHANGE,
                       u'订单发货成功[%s:%s]'%(company_name,out_sid))
                
    except Exception,exc:
        logger.error(u'发货异常:%s'%exc.message,exc_info=True)

    return trade_id
       
@task()
def regularRemainOrderTask():
    """更新定时提醒订单"""
    dt = datetime.datetime.now()
    MergeTrade.objects.filter(Q(remind_time__lte=dt)|Q(remind_time=None),
                              sys_status=pcfg.REGULAR_REMAIN_STATUS)\
                      .update(sys_status=pcfg.WAIT_AUDIT_STATUS)

@task
def saveTradeByTidTask(tid,seller_nick):
    user = User.objects.get(nick=seller_nick)
    Trade.get_or_create(tid,user.visitor_id)
    
@task()
def importTradeFromFileTask(fileName):
    """根据导入文件获取淘宝订单"""
    with open(fileName,'r') as f:
        for line in f:
            if not line:
                continue
            
            try:
                seller_nick,tid = line.split(',')
                if tid:
                    subtask(saveTradeByTidTask).delay(tid,
                                                      seller_nick.decode('gbk'))
            except:
                pass
    

@task()
def pushBuyerToCustomerTask(day):
    """ 将订单买家信息保存为客户信息 """
    
    dt = datetime.datetime.now()
    all_trades = MergeTrade.objects.filter(
                    created__gte=dt-datetime.timedelta(day,0,0)).order_by('-pay_time')
                
    for trade in all_trades:
        try:
            if not (trade.receiver_mobile or trade.receiver_phone):
                return 
       
            customer,state     = Customer.objects.get_or_create(
                                    nick=trade.buyer_nick,
                                    mobile=trade.receiver_mobile,
                                    phone=trade.receiver_phone)
            
            customer.name      = trade.receiver_name
            customer.zip       = trade.receiver_zip
            customer.address   = trade.receiver_address
            customer.city      = trade.receiver_city
            customer.state     = trade.receiver_state
            customer.district  = trade.receiver_district
            customer.save()
            
            trades        = MergeTrade.objects.filter(buyer_nick=self.buyer_nick,
                            receiver_mobile=trade.receiver_mobile,
                            status__in=pcfg.ORDER_SUCCESS_STATUS)\
                            .exclude(is_express_print=False,
                            sys_status=pcfg.FINISHED_STATUS).order_by('-pay_time')
            trade_num     = trades.count()
            
            if trades.count()>0 and trade_num != customer.buy_times:
                total_nums    =  trades.count()
                total_payment = trades.aggregate(total_payment=Sum('payment')).get('total_payment') or 0
                
                customer.last_buy_time = trades[0].pay_time
                customer.buy_times     = trades.count()
                customer.avg_payment   = float(round(float(total_payment)/total_nums,2))
                customer.save()
        except:
            pass
        
        




   
