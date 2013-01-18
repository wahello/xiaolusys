#-*- coding:utf8 -*-
import re
import datetime
import json
from django.http import HttpResponse
from django.db.models import Q,Sum
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from shopback.trades.models import MergeTrade,MergeOrder,GIFT_TYPE
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import Product,ProductSku
from shopback.base import log_action, User, ADDITION, CHANGE
from shopback.signals import rule_signal
from shopback import paramconfig as pcfg
from auth import apis
import logging

logger = logging.getLogger('trades.handler')

class CheckOrderView(ModelView):
    """ docstring for class CheckOrderView """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        
        rule_signal.send(sender='payment_rule',trade_tid=trade.tid)
        logistics = LogisticsCompany.objects.filter(status=True)
        
        trade_dict = {
            'id':trade.id,
            'tid':trade.tid,
            'buyer_nick':trade.buyer_nick,
            'seller_nick':trade.seller_nick,
            'pay_time':trade.pay_time,
            'payment':trade.payment,
            'post_fee':trade.post_fee,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'logistics_company':trade.logistics_company,
            'priority':trade.priority,
            'receiver_name':trade.receiver_name,
            'receiver_state':trade.receiver_state,
            'receiver_city':trade.receiver_city,
            'receiver_district':trade.receiver_district,
            'receiver_address':trade.receiver_address,
            'receiver_mobile':trade.receiver_mobile,
            'receiver_phone':trade.receiver_phone,
            'has_memo':trade.has_memo,
            'has_refund':trade.has_refund,
            'has_out_stock':trade.has_out_stock,
            'has_rule_match':trade.has_rule_match,
            'has_merge':trade.has_merge,
            'has_sys_err':trade.has_sys_err,
            'reason_code':trade.reason_code,
            'status':trade.status,
            'sys_status':trade.sys_status,
            'used_orders':trade.inuse_orders,
        }
        
        return {'trade':trade_dict,'logistics':logistics}
        
    def post(self, request, id, *args, **kwargs):
        
        user_id = request.user.id
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        
        priority      = request.POST.get('priority')
        logistic_code = request.POST.get('logistic_code')
        action_code   = request.POST.get('action')
        
        params = {}
        if priority:
            params['priority'] = priority
        if logistic_code:
            params['logistics_company'] = LogisticsCompany.objects.get(code=logistic_code)
        if params:
            MergeTrade.objects.filter(id=id).update(**params)
        if action_code == 'check':
            check_msg = []
            if trade.has_refund:
                check_msg.append("有待退款".decode('utf8'))
            if trade.has_out_stock :
                check_msg.append("有缺货".decode('utf8'))
            if trade.has_rule_match:
                check_msg.append("信息不全".decode('utf8'))
            if trade.sys_status != pcfg.WAIT_AUDIT_STATUS:
                check_msg.append("订单暂不能审核".decode('utf8'))
            if trade.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE):
                check_msg.append("需手动合单".decode('utf8'))
            if trade.has_reason_code(pcfg.POST_MODIFY_CODE) or trade.has_reason_code(pcfg.INVALID_END_CODE)\
                 or trade.has_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE) or trade.has_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)\
                 or trade.has_reason_code(pcfg.PAYMENT_RULE_ERROR_CODE) or trade.has_reason_code(pcfg.MERGE_TRADE_ERROR_CODE):
                check_msg.append("该订单需管理员审核".decode('utf8'))
            orders = trade.merge_trade_orders.filter(status=pcfg.WAIT_SELLER_SEND_GOODS)\
                        .exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)   
            if orders.count() <= 0:
                check_msg.append("没有可发订单！".decode('utf8'))
             
            if check_msg:
                return ','.join(check_msg)
            
            MergeTrade.objects.filter(id=id,sys_status = pcfg.WAIT_AUDIT_STATUS)\
                .update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,reason_code='')  
            log_action(user_id,trade,CHANGE,u'审核成功')
            
        elif action_code == 'review':
            if trade.sys_status != pcfg.WAIT_CHECK_BARCODE_STATUS:
                return u'不能复审'
            MergeTrade.objects.filter(id=id,sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS)\
                .update(can_review=True)
            log_action(user_id,trade,CHANGE,u'订单复审')
            
        return {'success':True}    
      
       
class OrderPlusView(ModelView):
    """ docstring for class OrderPlusView """
    
    def get(self, request, *args, **kwargs):
        
        q  = request.GET.get('q')
        if not q:
            return '没有输入查询关键字'.decode('utf8')
        products = Product.objects.filter(Q(outer_id=q)|Q(name__contains=q),status=pcfg.NORMAL)
        
        prod_list = [(prod.outer_id,prod.name,prod.price,[(sku.outer_id,sku.properties_name) for sku in 
                                                prod.prod_skus.filter(status=pcfg.NORMAL)]) for prod in products]
        return prod_list
        
    def post(self, request, *args, **kwargs):
        
        user_id  = request.user.id
        trade_id = request.POST.get('trade_id')
        outer_id = request.POST.get('outer_id')
        outer_sku_id = request.POST.get('outer_sku_id')
        num      = int(request.POST.get('num',1))    
        
        try:
            merge_trade = MergeTrade.objects.get(id=trade_id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        try:
            product = Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExist:
            return '该商品不存在'.decode('utf8')
        
        if outer_sku_id:
            try:
                prod_sku = ProductSku.objects.get(prod_outer_id=outer_id,outer_id=outer_sku_id)
            except ProductSku.DoesNotExist:
                return '该商品规格不存在'.decode('utf8')
        
        is_reverse_order = False
        if merge_trade.sys_status == pcfg.WAIT_CHECK_BARCODE_STATUS:
            merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
            is_reverse_order = True    
        
        merge_order = MergeOrder.gen_new_order(trade_id,outer_id,outer_sku_id,num,gift_type=pcfg.CS_PERMI_GIT_TYPE
                                               ,status=pcfg.WAIT_BUYER_CONFIRM_GOODS,is_reverse=is_reverse_order)
        
        log_action(user_id,merge_trade,ADDITION,u'添加子订单(%d)'%merge_order.id)
        
        return merge_order
    
           
def change_trade_addr(request):
    
    user_id  = request.user.id
    CONTENT    = request.REQUEST
    trade_id   = CONTENT.get('trade_id')
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"订单不存在！"}),mimetype="application/json")
        
    for (key, val) in CONTENT.items():
         setattr(trade, key, val)
    
    try:
        if trade.type in (pcfg.TAOBAO_TYPE,pcfg.FENXIAO_TYPE,pcfg.GUARANTEE_TYPE) and trade.sys_status==pcfg.WAIT_AUDIT_STATUS:
            response = apis.taobao_trade_shippingaddress_update(tid=trade.tid,
                                                            receiver_name=trade.receiver_name,
                                                            receiver_phone=trade.receiver_phone,
                                                            receiver_mobile=trade.receiver_mobile,
                                                            receiver_state=trade.receiver_state,
                                                            receiver_city=trade.receiver_city,
                                                            receiver_district=trade.receiver_district,
                                                            receiver_address=trade.receiver_address,
                                                            receiver_zip=trade.receiver_zip,
                                                            tb_user_id=trade.user.visitor_id)
    except Exception,exc:
        logger.error(exc.message,exc_info=True)
  
    trade.save()
    trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
    
    log_action(user_id,trade,CHANGE,u'修改地址')
    
    ret_params = {'code':0,'success':True}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")
    
    
def change_trade_order(request,id):
    
    user_id    = request.user.id
    CONTENT    = request.REQUEST
    outer_sku_id = CONTENT.get('outer_sku_id')
    order_num    = int(CONTENT.get('order_num',0))
    try:
        order = MergeOrder.objects.get(id=id)
    except MergeOrder.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"订单不存在！"}),mimetype="application/json")
    
    try:
        prod  = Product.objects.get(outer_id=order.outer_id)
    except Product.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"商品不存在！"}),mimetype="application/json")
        
    try:
        prod_sku = ProductSku.objects.get(prod_outer_id=order.outer_id,outer_id=outer_sku_id) 
    except ProductSku.DoesNotExist:
        return HttpResponse(json.dumps({'code':1,"response_error":"商品规格不存在！"}),mimetype="application/json")
    
    merge_trade = order.merge_trade
    is_reverse_order = False
    if merge_trade.sys_status == pcfg.WAIT_CHECK_BARCODE_STATUS:
        merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
        is_reverse_order = True
        
    order.outer_sku_id=prod_sku.outer_id
    order.sku_properties_name=prod_sku.properties_name
    order.is_rule_match = False
    order.out_stock     = False
    order.is_reverse_order = is_reverse_order
    order.num           = order_num
    order.save()
    merge_trade.remove_reason_code(pcfg.RULE_MATCH_CODE)
    MergeTrade.judge_out_stock(merge_trade.tid,None)
    order = MergeOrder.objects.get(id=order.id)
    
    log_action(user_id,merge_trade,CHANGE,u'修改子订单(%d)'%order.id)
    
    ret_params = {'code':0,'response_content':{'id':order.id,
                                               'outer_id':order.outer_id,
                                               'title':prod.name,
                                               'sku_properties_name':order.sku_properties_name,
                                               'num':order.num,
                                               'out_stock':order.out_stock,
                                               'price':order.price,
                                               'gift_type':order.gift_type,
                                               }}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

     
def delete_trade_order(request,id):
    
    user_id      = request.user.id
    try:
        merge_order  = MergeOrder.objects.get(id=id)
    except:
        HttpResponse(json.dumps({'code':1,'response_content':{'success':False}}),mimetype="application/json")
    
    merge_trade = merge_order.merge_trade
    is_reverse_order = False
    if merge_trade.sys_status == pcfg.WAIT_CHECK_BARCODE_STATUS:
        merge_trade.append_reason_code(pcfg.ORDER_ADD_REMOVE_CODE)
        is_reverse_order = True
        
    num = MergeOrder.objects.filter(id=id,status=pcfg.WAIT_SELLER_SEND_GOODS)\
        .update(sys_status=pcfg.INVALID_STATUS,is_reverse_order=is_reverse_order)
    if num == 1:
        log_action(user_id,merge_trade,CHANGE,u'设子订单无效(%d)'%merge_order.id)
        
        ret_params = {'code':0,'response_content':{'success':True}}
    else:
        ret_params = {'code':1,'response_content':{'success':False}}
        
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

    
        
############################### 订单复审 #################################       
class ReviewOrderView(ModelView):
    """ docstring for class ReviewOrderView """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return '该订单不存在'.decode('utf8')
        
        logistics = LogisticsCompany.objects.filter(status=True)
        order_nums = trade.inuse_orders.aggregate(total_num=Sum('num')).get('total_num')
        
        trade_dict = {
            'id':trade.id,
            'tid':trade.tid,
            'buyer_nick':trade.buyer_nick,
            'seller_nick':trade.seller_nick,
            'pay_time':trade.pay_time,
            'payment':trade.payment,
            'post_fee':trade.post_fee,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'logistics_company':trade.logistics_company,
            'out_sid':trade.out_sid,
            'consign_time':trade.consign_time,
            'priority':trade.priority,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'receiver_name':trade.receiver_name,
            'receiver_state':trade.receiver_state,
            'receiver_city':trade.receiver_city,
            'receiver_district':trade.receiver_district,
            'receiver_address':trade.receiver_address,
            'receiver_mobile':trade.receiver_mobile,
            'receiver_phone':trade.receiver_phone,
            'reason_code':trade.reason_code,
            'can_review':trade.can_review,
            'status':trade.status,
            'sys_status':trade.sys_status,
            'used_orders':trade.inuse_orders,
            'order_nums':order_nums,
            'new_memo':trade.has_reason_code(pcfg.NEW_MEMO_CODE),
            'new_refund':trade.has_reason_code(pcfg.WAITING_REFUND_CODE),
            'order_modify':trade.has_reason_code(pcfg.ORDER_ADD_REMOVE_CODE),
            'addr_modify':trade.has_reason_code(pcfg.ADDR_CHANGE_CODE),
        }
        
        return {'trade':trade_dict,'logistics':logistics}
        
    def post(self, request, id, *args, **kwargs):
        
        user_id  = request.user.id
        try:
            merge_trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return u'该订单不存在'
        
        if not merge_trade.can_review and merge_trade.sys_status \
            not in (pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
            return u'该订单不能复审'
        MergeTrade.objects.filter(id=id).update(reason_code='')
        
        log_action(user_id,merge_trade,ADDITION,u'复审通过')
        
        return {'success':True}
    
    
def change_logistic_and_outsid(request):
    
    user_id  = request.user.id
    CONTENT    = request.REQUEST
    trade_id   = CONTENT.get('trade_id')
    out_sid    = CONTENT.get('out_sid')
    logistic_code = CONTENT.get('logistic_code','').upper()
    
    if not trade_id or not out_sid or not logistic_code:
        ret_params = {'code':1,'response_content':u'请填写快递名称及单号'}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
    
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
    except:    
        ret_params = {'code':1,'response_content':u'未找到该订单'}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
        
    try:
        logistic   = LogisticsCompany.objects.get(code=logistic_code)
        logistic_regex = re.compile(logistic.reg_mail_no)
        if merge_trade.sys_status == pcfg.WAIT_CHECK_BARCODE_STATUS and logistic_regex.match(out_sid): 
            try:
                response = apis.taobao_logistics_consign_resend(tid=merge_trade.tid,out_sid=out_sid
                                                 ,company_code=logistic_code,tb_user_id=merge_trade.user.visitor_id)
                if not response['logistics_consign_resend_response']['shipping']['is_success']:
                    raise Exception(u'重发失败')
            except Exception,exc:
                dt  = datetime.datetime.now()
                merge_trade.sys_memo = u'%s,修改单号[%s]:(%s)%s'%(merge_trade.sys_memo,
                                                             dt.strftime('%Y-%m-%d %H:%M'),logistic_code,out_sid)
                logger.error(exc.message,exc_info=True)
                
            merge_trade.logistics_company = logistic
            merge_trade.out_sid   = out_sid
            merge_trade.save()
            
            log_action(user_id,merge_trade,CHANGE,u'复审修改快递及单号(修改前:%s,%s)'%(logistic_code,out_sid))
        else:
            raise Exception(u'快递单号不匹配')
    except Exception,exc:
        ret_params = {'code':1,'response_content':exc.message}
        return HttpResponse(json.dumps(ret_params),mimetype="application/json")
        
    ret_params = {'code':0,'response_content':{'logistic_company_name':logistic.name
                                               ,'logistic_company_code':logistic.code,'out_sid':out_sid}}
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

