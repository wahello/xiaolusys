# coding:utf-8
import datetime
import json
from operator import itemgetter
import re
import time

from django.contrib.auth.models import User
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, Q, Sum, Count
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import api_view, renderer_classes, list_route, detail_route
from rest_framework.response import Response
from rest_framework.views import APIView

from flashsale.dinghuo import paramconfig as pcfg
from flashsale.dinghuo import log_action, CHANGE
from flashsale.dinghuo.models import (orderdraft, OrderDetail, OrderList,
                                      InBound, InBoundDetail, OrderListInBound,
                                      OrderDetailInBoundDetail)
from flashsale.dinghuo.models_stats import SupplyChainDataStats
from shopback.items.models import Product, ProductCategory, ProductSku, ProductStock
from supplychain.supplier.models import SaleProduct, SaleSupplier


from . import forms, functions, functions2view, models


def search_product(request):
    """搜索商品"""
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    product_id_from_page = request.GET.get("searchtext", "")
    product_id_from_page = product_id_from_page.strip()
    product_result = Product.objects.filter(Q(
        outer_id__icontains=product_id_from_page) | Q(name__icontains=
                                                      product_id_from_page))
    product_list = functions.get_product_dict_from_product(product_result)
    data = json.dumps(product_list, cls=DjangoJSONEncoder)
    return HttpResponse(data)


@csrf_exempt
def init_draft(request):
    """初始化购物车"""
    user = request.user
    if request.method == "POST":
        post = request.POST
        product_counter = int(post["product_counter"])
        for i in range(1, product_counter + 1):
            product_id_index = "product_id_" + str(i)
            product_id = post[product_id_index]
            all_sku = ProductSku.objects.filter(product_id=product_id,
                                                status="normal")
            for pro_sku in all_sku:
                sku_quantity_index = product_id + "_tb_quantity_" + str(
                    pro_sku.id)
                sku_quantity = post[sku_quantity_index]
                mai_ru_jia_ge_index = product_id + "_tb_cost_" + str(pro_sku.id)
                mai_ru_jia_ge = post[mai_ru_jia_ge_index]
                mai_ru_jia_ge = float(mai_ru_jia_ge)
                if sku_quantity and mai_ru_jia_ge and mai_ru_jia_ge != 0 and sku_quantity != "0":
                    sku_quantity = int(sku_quantity)
                    mai_ru_jia_ge = float(mai_ru_jia_ge)
                    p1 = Product.objects.get(id=product_id)
                    draft_query = orderdraft.objects.filter(
                        buyer_name=user,
                        product_id=product_id,
                        chichu_id=pro_sku.id)
                    if draft_query.count() > 0:
                        draft_query[0].buy_quantity = draft_query[
                            0].buy_quantity + sku_quantity
                        draft_query[0].save()
                    else:
                        current_time = datetime.datetime.now()
                        t_draft = orderdraft(buyer_name=user,
                                             product_id=product_id,
                                             outer_id=p1.outer_id,
                                             buy_quantity=sku_quantity,
                                             product_name=p1.name,
                                             buy_unitprice=mai_ru_jia_ge,
                                             chichu_id=pro_sku.id,
                                             product_chicun=pro_sku.name,
                                             created=current_time)
                        t_draft.save()
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")
    else:
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")


@csrf_exempt
def new_order(request):
    """从购物车生成订单"""
    username = request.user

    buyer_name = '%s%s' % (request.user.last_name, request.user.first_name)
    buyer_name = buyer_name or request.user.username
    all_drafts = orderdraft.objects.all().filter(buyer_name=username)
    express = OrderList.EXPRESS_CONPANYS
    if request.method == 'POST':
        post = request.POST
        type_of_order = post['type_of_order']
        p_district = post['p_district']
        costofems = post['costofems']
        if costofems == "":
            costofems = 0
        else:
            costofems = float(costofems)
        current_time = datetime.datetime.now()
        receiver = post['consigneeName']
        supplierId = post['supplierId']
        storehouseId = post['storehouseId']
        express_company = post['express_company']
        express_no = post['express_no']
        businessDate = datetime.datetime.now()
        remarks = post['remarks']
        amount = functions.cal_amount(username, costofems)
        orderlist = OrderList()
        orderlist.buyer_name = username
        orderlist.costofems = costofems * 100
        orderlist.receiver = receiver
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.supplier_name = supplierId
        orderlist.p_district = p_district
        orderlist.created = businessDate
        orderlist.updated = businessDate
        if len(remarks.strip()) > 0:
            orderlist.note = "-->" + request.user.username + " : " + remarks
        orderlist.status = pcfg.SUBMITTING
        if type_of_order == '2':
            orderlist.status = '7'
            already = OrderList.objects.filter(buyer_name=username,
                                               status='7',
                                               created=businessDate)
            if already.count() > 0:
                return HttpResponse('''<div style='position: absolute;top: 40%;
                        left: 35%;
                        width: 630px;
                        margin: -20px 0 0 -75px;
                        padding: 0 10px;
                        background: #eee;
                        line-height: 2.4;'>
                        您今天已经拍过样品的订货单了，请到订货单号为<a style='font-size: 40px' href='/sale/dinghuo/changedetail/{0}' target='_blank'>{0}</a>添加样品</div>'''
                                    .format(already[0].id))
        orderlist.order_amount = amount
        orderlist.save()


        drafts = orderdraft.objects.filter(buyer_name=username)
        for draft in drafts:
            total_price = draft.buy_quantity * draft.buy_unitprice
            orderdetail1 = OrderDetail()
            orderdetail1.orderlist_id = orderlist.id
            orderdetail1.product_id = draft.product_id
            orderdetail1.outer_id = draft.outer_id
            orderdetail1.product_name = draft.product_name
            orderdetail1.product_chicun = draft.product_chicun
            orderdetail1.chichu_id = draft.chichu_id
            orderdetail1.buy_quantity = draft.buy_quantity
            orderdetail1.total_price = total_price
            orderdetail1.buy_unitprice = draft.buy_unitprice
            orderdetail1.created = current_time
            orderdetail1.updated = current_time
            orderdetail1.save()

        products_dict = {}
        for draft in drafts:
            pid = int(draft.product_id)
            products_dict[pid] = products_dict.get(pid, 0) + 1
        saleproducts_dict = {}
        for product in Product.objects.filter(id__in=products_dict.keys()):
            saleproducts_dict[product.sale_product] = saleproducts_dict.get(product.sale_product, 0) + products_dict[product.id]
        suppliers_dict = {}
        for saleproduct in SaleProduct.objects.filter(id__in=saleproducts_dict.keys()):
            suppliers_dict[saleproduct.sale_supplier_id] = suppliers_dict.get(saleproduct.sale_supplier_id, 0) + saleproducts_dict[saleproduct.id]
        if suppliers_dict:
            supplier_id, _ = max(suppliers_dict.items(), key=itemgetter(1))
            if supplier_id:
                orderlist.supplier_id = supplier_id
        orderlist.buyer_id = request.user.id
        orderlist.save()

        drafts.delete()
        log_action(request.user.id, orderlist, CHANGE, u'新建订货单')
        return HttpResponseRedirect("/sale/dinghuo/changedetail/" + str(
            orderlist.id))
    else:
        drafts = orderdraft.objects.filter(buyer_name=username)
        supplier_name = ''
        products_dict = {}
        for draft in drafts:
            pid = int(draft.product_id)
            products_dict[pid] = products_dict.get(pid, 0) + 1
        saleproducts_dict = {}
        for product in Product.objects.filter(id__in=products_dict.keys()):
            saleproducts_dict[product.sale_product] = saleproducts_dict.get(product.sale_product, 0) + products_dict[product.id]
        suppliers_dict = {}
        for saleproduct in SaleProduct.objects.filter(id__in=saleproducts_dict.keys()):
            suppliers_dict[saleproduct.sale_supplier_id] = suppliers_dict.get(saleproduct.sale_supplier_id, 0) + saleproducts_dict[saleproduct.id]
        if suppliers_dict:
            supplier_id, _ = max(suppliers_dict.items(), key=itemgetter(1))
            sale_suppliers = SaleSupplier.objects.filter(id=supplier_id)
            if sale_suppliers:
                sale_supplier = sale_suppliers[0]
                supplier_name = sale_supplier.supplier_name


    return render_to_response('dinghuo/shengchengorder.html',
                              {"orderdraft": all_drafts,
                               "express": express, 'buyer_name': buyer_name, 'supplier_name': supplier_name},
                              context_instance=RequestContext(request))


def del_draft(request):
    username = request.user
    drafts = orderdraft.objects.filter(buyer_name=username)
    drafts.delete()
    return HttpResponse("")


def add_purchase(request, outer_id):
    user = request.user
    order_dr_all = orderdraft.objects.all().filter(buyer_name=user)
    product_res = []
    queryset = Product.objects.filter(status=Product.NORMAL,
                                      outer_id__icontains=outer_id)
    for p in queryset:
        product_dict = model_to_dict(p)
        product_dict['prod_skus'] = []
        guiges = ProductSku.objects.filter(product_id=p.id).exclude(
            status=u'delete')
        for guige in guiges:
            sku_dict = model_to_dict(guige)
            sku_dict['name'] = guige.name
            sku_dict['wait_post_num'] = functions2view.get_lack_num_by_product(
                p, guige)
            product_dict['prod_skus'].append(sku_dict)
        product_res.append(product_dict)
    return render_to_response("dinghuo/addpurchasedetail.html",
                              {"productRestult": product_res,
                               "drafts": order_dr_all},
                              context_instance=RequestContext(request))


@csrf_exempt
def data_chart(req):
    content = req.REQUEST
    today = datetime.date.today()
    start_time_str = content.get("df", None)
    end_time_str = content.get("dt", None)
    if start_time_str:
        year, month, day = start_time_str.split('-')
        start_date = datetime.date(int(year), int(month), int(day))
        if start_date > today:
            start_date = today
    else:
        start_date = today - datetime.timedelta(days=7)
    if end_time_str:
        year, month, day = end_time_str.split('-')
        end_date = datetime.date(int(year), int(month), int(day))
        if end_date > today:
            end_date = today
    else:
        end_date = today
    a_data = SupplyChainDataStats.objects.filter(
        group=u'采购A',
        stats_time__range=(start_date, end_date)).order_by('stats_time')
    b_data = SupplyChainDataStats.objects.filter(
        group=u'采购B',
        stats_time__range=(start_date, end_date)).order_by('stats_time')
    c_data = SupplyChainDataStats.objects.filter(
        group=u'采购C',
        stats_time__range=(start_date, end_date)).order_by('stats_time')

    return render_to_response("dinghuo/data_grape.html",
                              {"a_data": a_data,
                               "b_data": b_data,
                               "c_data": c_data,
                               "start_date": start_date,
                               "end_date": end_date},
                              context_instance=RequestContext(req))


@csrf_exempt
def plus_quantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = orderdraft.objects.get(id=draft_id)
    draft.buy_quantity = draft.buy_quantity + 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def plusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(
        buy_quantity=F('buy_quantity') + 1)
    OrderDetail.objects.filter(id=orderdetailid).update(
        total_price=F('total_price') + orderdetail.buy_unitprice)
    OrderList.objects.filter(id=orderdetail.orderlist_id).update(
        order_amount=F('order_amount') + orderdetail.buy_unitprice)
    log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}{2}'.format(
        (u'加一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'加一'))
    return HttpResponse("OK")


@csrf_exempt
def minusquantity(req):
    post = req.POST
    draft_id = post["draftid"]
    draft = orderdraft.objects.get(id=draft_id)
    draft.buy_quantity = draft.buy_quantity - 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def minusordertail(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.filter(id=orderdetailid)
    if orderdetail.count() > 0:
        order_detail = orderdetail[0]
        order_list = OrderList.objects.get(id=order_detail.orderlist_id)
        OrderDetail.objects.filter(id=orderdetailid).update(
            buy_quantity=F('buy_quantity') - 1)
        OrderDetail.objects.filter(id=orderdetailid).update(
            total_price=F('total_price') - order_detail.buy_unitprice)
        OrderList.objects.filter(id=order_detail.orderlist_id).update(
            order_amount=F('order_amount') - order_detail.buy_unitprice)
        log_action(req.user.id, order_list, CHANGE, u'订货单{0}{1}{2}'.format(
            (u'减一件'), order_detail.product_name, order_detail.product_chicun))
        log_action(req.user.id, order_detail, CHANGE, u'%s' % (u'减一'))
        if order_detail.buy_quantity == 1:
            order_detail.delete()
            return HttpResponse("deleted")
        return HttpResponse("OK")
    else:
        return HttpResponse("false")


@csrf_exempt
def minusarrived(req):
    post = req.POST
    orderdetailid = post["orderdetailid"]
    orderdetail = OrderDetail.objects.get(id=orderdetailid)
    orderlist = OrderList.objects.get(id=orderdetail.orderlist_id)
    OrderDetail.objects.filter(id=orderdetailid).update(
        arrival_quantity=F('arrival_quantity') - 1)
    OrderDetail.objects.filter(id=orderdetailid).update(non_arrival_quantity=F(
        'buy_quantity') - F('arrival_quantity') - F('inferior_quantity'))
    ProductStock.add_order_detail(orderdetail, -1)
    log_action(req.user.id, orderlist, CHANGE,
               u'订货单{0}{1}{2}'.format((u'入库减一件'), orderdetail.product_name, orderdetail.product_chicun))
    log_action(req.user.id, orderdetail, CHANGE, u'%s' % (u'入库减一'))
    return HttpResponse("OK")


@csrf_exempt
def removedraft(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.delete()
    return HttpResponse("OK")


@csrf_exempt
def viewdetail(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    express = OrderList.EXPRESS_CONPANYS
    return render_to_response("dinghuo/orderdetail.html",
                              {"orderlist": orderlist,
                               "orderdetails": orderdetail,
                               "express": express},
                              context_instance=RequestContext(req))


@csrf_exempt
def detaillayer(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    return render_to_response("dinghuo/layerdetail.html",
                              {"orderlist": orderlist,
                               "orderdetails": orderdetail},
                              context_instance=RequestContext(req))


@csrf_exempt
def changestatus(req):
    post = req.POST
    orderid = post["orderid"]
    status_text = post["func"]
    orderlist = OrderList.objects.get(id=orderid)
    orderlist.status = status_text
    orderlist.save()
    state = True
    if status_text == "审核":
        state = True
    else:
        state = False
    log_action(req.user.id, orderlist, CHANGE,
               u'%s订货单' % (state and u'审核' or u'作废'))
    return HttpResponse("OK")


@csrf_exempt
def setusertogroup(req):
    post = req.POST
    groupid = post.get("groupid", 0)
    uid = post["uid"]
    myuser = MyUser.objects.filter(user_id=int(uid))
    if myuser.count() > 0:
        myusertemp = myuser[0]
        myusertemp.group_id = int(groupid)
        myusertemp.save()
    else:
        MyUser(user_id=int(uid), group_id=int(groupid)).save()
    return HttpResponse("OK")


@csrf_exempt
def modify_order_list(req):
    post = req.POST
    order_list_id = post.get("orderlistid", 0)
    receiver = post['receiver']
    supplier_name = post['supplier_name']
    express_company = post['express_company']
    express_no = post['express_no']
    note = post.get('note', "")
    if len(note) > 0:
        note = "\n" + "-->" + datetime.datetime.now().strftime(
            '%m月%d %H:%M') + req.user.username + ":" + note
    order_amount = post['order_amount']
    try:
        orderlist = OrderList.objects.get(id=order_list_id)
        orderlist.receiver = receiver
        orderlist.supplier_name = supplier_name
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.note = orderlist.note + note
        orderlist.order_amount = order_amount
        orderlist.save()
        log_action(req.user.id, orderlist, CHANGE, u'修改订货单')
    except:
        return HttpResponse("False")
    return HttpResponse("OK")


@csrf_exempt
def add_detail_to_ding_huo(req):
    post = req.POST
    buy_quantity = post["buy_quantity"]
    buy_price = post["buy_price"]
    orderlistid = post["orderlistid"]
    sku_id = post["sku_id"]
    if len(buy_quantity.strip()) > 0 and len(buy_price.strip()) > 0 and len(
            orderlistid.strip()) > 0 and len(sku_id.strip()) > 0:
        buy_quantity, buy_price, orderlistid, sku_id = int(buy_quantity), float(
            buy_price), int(orderlistid), int(sku_id)
        pro_sku = ProductSku.objects.get(id=sku_id)
        product_id = pro_sku.product_id
        outer_id = pro_sku.product.outer_id
        product_name = pro_sku.product.name
        orderlist = OrderList.objects.get(id=orderlistid)
        product_chicun = pro_sku.properties_alias if len(
            pro_sku.properties_alias) > 0 else pro_sku.properties_name
        order = OrderDetail.objects.filter(orderlist_id=orderlistid,
                                           chichu_id=sku_id,
                                           buy_unitprice=buy_price)
        if order.count() > 0:
            ordertemp = order[0]
            ordertemp.buy_quantity = ordertemp.buy_quantity + buy_quantity
            ordertemp.total_price = ordertemp.total_price + buy_quantity * buy_price
            ordertemp.save()
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format(
                (u'加一件'), ordertemp.product_name))
        else:
            order_new = OrderDetail()
            order_new.orderlist_id = orderlistid
            order_new.product_id = product_id
            order_new.outer_id = outer_id
            order_new.product_name = product_name
            order_new.chichu_id = sku_id
            order_new.product_chicun = product_chicun
            order_new.buy_quantity = buy_quantity
            order_new.buy_unitprice = buy_price
            order_new.total_price = buy_price * buy_quantity
            order_new.save()
            log_action(req.user.id, orderlist, CHANGE, u'订货单{0}{1}'.format(
                (u'加一件'), order_new.product_name))
        return HttpResponse("OK")
    return HttpResponse("False")


@csrf_exempt
def changearrivalquantity(request):
    """
    修改入库存数量
    1、增加后为负数不予添加
    """
    post = request.POST
    order_detail_id = post.get("orderdetailid", "").strip()
    arrived_num = post.get("arrived_num", "0").strip()  #获取即将入库的数量
    result = "{flag:false,num:0}"
    arrival_time = datetime.datetime.now()
    if len(arrived_num) > 0 and len(order_detail_id) > 0:
        arrived_num = int(arrived_num)
        order_detail_id = int(order_detail_id)
        order = OrderDetail.objects.get(id=order_detail_id)
        orderlist = OrderList.objects.get(id=order.orderlist_id)
        try:
            sku = ProductSku.objects.get(id=order.chichu_id)
            if sku.quantity + arrived_num < 0:
                return HttpResponse(result)
        except:
            return HttpResponse(result)
        order.arrival_quantity = order.arrival_quantity + arrived_num
        order.non_arrival_quantity = order.buy_quantity - order.arrival_quantity - order.inferior_quantity
        ProductStock.add_order_detail(order, arrived_num)
        order.arrival_time = arrival_time
        order.save()
        result = "{flag:true,num:" + str(order.arrival_quantity) + "}"
        log_action(request.user.id, orderlist, CHANGE,
                   u'订货单{0}{1}入库{2}件'.format(order.product_name,
                                             order.product_chicun, arrived_num))
        return HttpResponse(result)

    return HttpResponse(result)


class DailyDingHuoStatsView(View):

    def get(self, request):
        content = request.REQUEST
        daystr = content.get("day", None)
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day

        target_date = today
        if daystr:
            year, month, day = daystr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month,
                                      target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month,
                                    target_date.day, 23, 59, 59)

        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        orderlists = OrderList.objects.exclude(status=u'作废').exclude(
            status=u'7').filter(created=target_date)
        orderlists_list = []
        for orderlist in orderlists:
            orderlist_dict = model_to_dict(orderlist)
            orderlist_dict['orderdetail'] = []

            orderdetails = OrderDetail.objects.filter(orderlist_id=orderlist.id)
            list = []
            for orderdetail in orderdetails:
                orderdetailouter_id = orderdetail.outer_id
                searchouterid = orderdetailouter_id[0:len(str(
                    orderdetailouter_id)) - 1]
                list.append(searchouterid)
            list = {}.fromkeys(list).keys()

            for listbean in list:
                temporder = orderdetails.filter(outer_id__icontains=listbean)
                tempproduct = Product.objects.filter(
                    outer_id__icontains=listbean)
                count_quantity = 0
                count_price = 0
                temp_dict = {}
                for order in temporder:
                    count_quantity += order.buy_quantity
                    count_price += order.total_price
                product_name = temporder[0].product_name.split('-')
                if tempproduct.count() > 0:
                    temp_dict['pic_path'] = tempproduct[0].pic_path
                else:
                    temp_dict['pic_path'] = ""
                temp_dict['product_name'] = product_name[0]
                temp_dict['outer_id_p'] = listbean
                temp_dict['quantity'] = count_quantity
                temp_dict['price'] = count_price
                orderlist_dict['orderdetail'].append(temp_dict)
            if orderlist.status == u"草稿":
                orderlist_dict['statusflag'] = True
            else:
                orderlist_dict['statusflag'] = False
            orderlists_list.append(orderlist_dict)
        return render_to_response("dinghuo/dailystats.html",
                                  {"orderlists_lists": orderlists_list,
                                   "prev_day": prev_day,
                                   "target_date": target_date,
                                   "next_day": next_day},
                                  context_instance=RequestContext(request))


import flashsale.dinghuo.utils as tools


class StatsByProductIdView(View):

    def getUserName(self, uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'

    def get(self, request, product_id):
        pro_bean = Product.objects.filter(id=product_id, status=Product.NORMAL)
        dinghuo_begin_str = request.GET.get("showt_begin")
        dinghuo_begin = ""
        if pro_bean.count() > 0:
            if not dinghuo_begin_str:
                dinghuo_begin = pro_bean[0].sale_time
            else:
                dinghuo_begin = tools.parse_date(dinghuo_begin_str)

            order_details = OrderDetail.objects.exclude(
                orderlist__status=u'作废').filter(product_id=product_id).filter(
                    orderlist__created__gte=dinghuo_begin)

        return render_to_response("dinghuo/productstats.html",
                                  {"orderdetails": order_details,
                                   "dinghuo_begin": dinghuo_begin,
                                   "product_id": product_id},
                                  context_instance=RequestContext(request))


from flashsale.dinghuo.models_user import MyUser, MyGroup
from django.db import connection


class DailyWorkView(View):

    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.REQUEST
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        groupname = content.get("groupname", 0)
        groupname = int(groupname)
        search_text = content.get("search_text", '').strip()
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        shelve_from = datetime.datetime(target_date.year, target_date.month,
                                        target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from < datetime.timedelta(0):
            time_to = shelve_from + datetime.timedelta(1)
        query_time = self.parseEndDt(query_time_str)
        order_sql = "select id,outer_id,sum(num) as sale_num,pay_time from " \
                    "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                    "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                    "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                    "and sys_status not in('INVALID','ON_THE_FLY') " \
                    "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                    "and gift_type !=4 " \
                    "and (pay_time between '{0}' and '{1}') " \
                    "and char_length(outer_id)>=9 " \
                    "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                    "group by outer_id".format(shelve_from, time_to)

        if groupname == 0:
            group_sql = ""
        else:
            group_sql = "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser where group_id =" + str(
                groupname) + "))"
        if len(search_text) > 0:
            search_text = str(search_text)
            product_sql = "select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where status='normal' and outer_id like '%%{0}%%' or name like '%%{0}%%'".format(
                search_text)
        else:
            product_sql = "select id,name as product_name,outer_id,pic_path,cost, agent_price,category_id from " \
                          "shop_items_product where  sale_time='{0}' and status!='delete' {1}".format(
                target_date, group_sql)
        sql = "select product.outer_id,product.product_name,product.pic_path," \
              "order_info.sale_num,product.id,product.cost,product.agent_price,product.category_id " \
              "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id "

        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        trade_dict = {}

        for product in raw:
            sale_num = int(product[3] or 0)
            outer_id = product[0]
            cost = product[5]
            agent_price = product[6]
            category = product[7]
            temp_dict = {"outer_id": product[0],
                         "product_id": product[4],
                         "product_name": product[1].split("/")[0],
                         "pic_path": product[2],
                         "sale_num": sale_num or 0,
                         "cost": cost,
                         "agent_price": agent_price,
                         "category": category}
            pro_id = outer_id[0:len(outer_id) - 1]
            if pro_id not in trade_dict:
                trade_dict[pro_id] = temp_dict
            else:
                trade_dict[pro_id]['sale_num'] += sale_num
        trade_dict = sorted(trade_dict.items(),
                            key=lambda d: d[1]['sale_num'],
                            reverse=True)
        return render_to_response("dinghuo/dailywork.html",
                                  {"target_product": trade_dict,
                                   "shelve_from": target_date,
                                   "time_to": time_to,
                                   "searchDinghuo": query_time,
                                   'groupname': groupname,
                                   "search_text": search_text},
                                  context_instance=RequestContext(request))


def get_category(category):
    if not category.parent_cid:
        return unicode(category.name)
    try:
        p_cat = category.__class__.objects.get(cid=category.parent_cid).name
    except:
        p_cat = u'--'
    return p_cat


class ProductCategoryAPIView(generics.ListCreateAPIView):
    """

    """
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        product = request.GET.get("product")
        category = request.GET.get("category")
        kucun = 0
        all_product = Product.objects.filter(status=Product.NORMAL,
                                             outer_id__startswith=product)
        for one_product in all_product:
            kucun += one_product.collect_num
        try:
            category_bean = ProductCategory.objects.get(cid=category)
            group = get_category(category_bean)
            category = category_bean.__unicode__()
        except:
            return Response({"flag": "error"})
        return Response({"flag": "done",
                         "group": group,
                         "category": category,
                         "stock": kucun})


class PendingDingHuoViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.OrderList.objects.all()
    template_name = 'dinghuo/pending_dinghuo.html'

    def list(self, request, *args, **kwargs):
        if not re.search(r'application/json', request.META['HTTP_ACCEPT']):
            return Response()

        now = datetime.datetime.now()
        items = []

        status_mapping = {'5': '有次品', '6': '到货有问题', '7': '样品'}
        for order_list in models.OrderList.objects \
            .exclude(status__in=[models.OrderList.COMPLETED, models.OrderList.ZUOFEI]) \
            .order_by('-updated'):
            items.append({
                'id': order_list.id,
                'receiver': order_list.receiver,
                'order_amount': round(order_list.order_amount, 2),
                'supplier_name': order_list.supplier_name,
                'supplier_shop': order_list.supplier_shop,
                'status': order_list.status,
                'pay_status': order_list.pay_status,
                'p_district': order_list.p_district,
                'created': order_list.created,
                'updated': {
                    'display': order_list.updated.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': time.mktime(order_list.updated.timetuple())
                },
                'memo': order_list.note.replace('\r\n', '<br>').replace('\n',
                                                                        '<br>')
            })

        order_stat_mapping = {}
        for stat in models.OrderDetail.objects \
          .filter(orderlist_id__in=map(lambda x: x['id'], items)) \
          .values('orderlist_id') \
          .annotate(model_count=Count('outer_id', distinct=True), quantity=Sum('buy_quantity')):
            order_stat_mapping[stat['orderlist_id']] = stat

        for item in items:
            item['up_to_today'] = (now.date() - item['created']).days
            item['created'] = item['created'].strftime('%Y-%m-%d')
            if item['p_district'] == '3':
                item['warehouse'] = '广州'
            else:
                item['warehouse'] = '上海'
            if item['status'] in status_mapping.keys():
                item['status'] = status_mapping[item['status']]
            order_list_stat = order_stat_mapping.get(item['id']) or {}
            item['model_count'] = order_list_stat.get('model_count') or 0
            item['quantity'] = order_list_stat.get('quantity') or 0
            item['pay_status'] = item.get('pay_status') or '正常'
        return Response({'data': items})


class DingHuoOrderListViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.OrderList.objects.all()

    EXPRESS_NO_SPLIT_PATTERN = re.compile(r'\s+|,')
    MEMO_TPL = '编码:%(outer_id)s 商品名:%(product_name)s 规格:%(properties_name)s %(msg)s'

    ORDERDETAIL_OP_LOG_TPL = '订货单明细ID:%(id)d %(msg)s'
    ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL = '入库操作记录ID:%(id)d %(msg)s'
    INBOUNDDETAIL_OP_LOG_TPL = '入库明细ID:%(id)d %(msg)s'

    @detail_route(methods=['post'])
    def change_buyer(self, request, pk):
        buyer_id = int(request.POST.get('buyer_id') or 0)
        models.OrderList.objects.filter(id=pk).update(buyer=buyer_id)
        return Response(buyer_id)

    @list_route(methods=['post'])
    def edit_supplier_inbound(self, request):
        form = forms.EditInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'error': '参数错误'})

        if not form.cleaned_attrs.inbound_id:
            return Response({'error': '入仓单不存在'})

        inbounds = InBound.objects.filter(
            id=form.cleaned_attrs.inbound_id)[:1]
        if not inbounds:
            return Response({'error': '入仓单不存在'})
        inbound = inbounds[0]


        inbound_skus_dict = json.loads(form.cleaned_attrs.skus)
        if not inbound_skus_dict:
            return Response({'error': '请点击作废按钮'})
        inbound_skus_dict = {int(k): v
                             for k, v in inbound_skus_dict.iteritems()}

        op_logs = []
        skus_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            skus_dict[sku.id] = {
                'product_id': sku.product.id,
                'sku_id': sku.id,
                'outer_id': sku.product.outer_id,
                'product_name': sku.product.name,
                'properties_name': sku.properties_name or
                sku.properties_alias or '',
                'quantity': sku.quantity
            }

        inbound_details = {}
        for inbound_detail in inbound.details.filter(
                status=InBoundDetail.NORMAL):
            inbound_details[inbound_detail.sku_id] = inbound_detail

        for sku_id in inbound_skus_dict.keys():
            inbound_sku_dict = inbound_skus_dict[sku_id]
            sku_dict = skus_dict.get(sku_id)
            if not sku_dict:
                continue
            product_id = sku_dict['product_id']
            outer_id = sku_dict['outer_id']
            product_name = sku_dict['product_name']
            properties_name = sku_dict['properties_name']
            arrival_quantity = inbound_sku_dict['arrival_quantity']
            inferior_quantity = inbound_sku_dict['inferior_quantity']

            inbound_sku_dict.update({
                'outer_id': outer_id,
                'product_name': product_name,
                'properties_name': properties_name
            })

            inbound_detail = inbound_details.get(sku_id)
            if inbound_detail:
                if inbound_detail.arrival_quantity == arrival_quantity and \
                  inbound_detail.inferior_quantity == inferior_quantity:
                    inbound_skus_dict.pop(sku_id, False)
                    continue
                else:
                    orderlist_ids = set()
                    for record in inbound_detail.records.filter(
                            status=OrderDetailInBoundDetail.NORMAL):
                        record.status = OrderDetailInBoundDetail.INVALID
                        record.save()
                        op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL % {'id': record.id, 'msg': '设为无效'})

                        if record.arrival_quantity:
                            record.orderdetail.arrival_quantity -= record.arrival_quantity
                            op_logs.append(
                                self.ORDERDETAIL_OP_LOG_TPL % {'id': record.orderdetail.id, 'msg': '到货数-%d' % record.arrival_quantity}
                            )
                        if record.inferior_quantity:
                            record.orderdetail.inferior_quantity -= record.inferior_quantity
                            op_logs.append(
                                self.ORDERDETAIL_OP_LOG_TPL % {'id': record.orderdetail.id, 'msg': '次品数-%d' % record.arrival_quantity}
                            )
                        orderlist_ids.add(record.orderdetail.orderlist_id)
                        record.orderdetail.save()
                    if arrival_quantity or inferior_quantity:
                        inbound_detail.arrival_quantity = arrival_quantity
                        inbound_detail.inferior_quantity = inferior_quantity
                        inbound_detail.save()
                        op_logs.append(
                            self.INBOUNDDETAIL_OP_LOG_TPL % {'id': inbound_detail.id, 'msg': '更新 到货数%d 次品数%d' % (arrival_quantity, inferior_quantity)}
                        )
                    else:
                        inbound_detail_id = inbound_detail.id
                        inbound_detail.delete()
                        op_logs.append(
                            self.INBOUNDDETAIL_OP_LOG_TPL % {'id': inbound_detail_id, 'msg': '删除'}
                        )
                    #Todo: update orderlist status
            else:
                inbound_detail = InBoundDetail(
                    inbound=inbound,
                    product_id=product_id,
                    sku_id=sku_id,
                    product_name=product_name,
                    outer_id=outer_id,
                    properties_name=properties_name,
                    arrival_quantity=arrival_quantity,
                    inferior_quantity=inferior_quantity)
                inbound_detail.save()
                op_logs.append(
                    self.INBOUNDDETAIL_OP_LOG_TPL % {'id': inbound_detail.id, 'msg': '创建 到货数%d 次品数%d' % (arrival_quantity, inferior_quantity)}
                )
                inbound_details[sku_id] = inbound_detail

        orderlists_with_express_no = []
        orderlists_without_express_no = []
        for orderlist in OrderList.objects.filter(supplier_id=form.cleaned_attrs.target_id) \
          .exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]).order_by('created'):
            if form.cleaned_attrs.express_no and orderlist.express_no:
                if form.cleaned_attrs.express_no.strip() in \
                    self.EXPRESS_NO_SPLIT_PATTERN.split(orderlist.express_no.strip()):
                    orderlists_with_express_no.append(orderlist)
                    continue
            orderlists_without_express_no.append(orderlist)

        op_logs.append('重新分配入库单...')
        len_of_op_logs = len(op_logs)
        orderlists = orderlists_with_express_no + orderlists_without_express_no
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                inbound_detail = inbound_details.get(sku_id)
                if not (inbound_detail and inbound_sku_dict):
                    continue
                plan_quantity = orderdetail.buy_quantity - orderdetail.arrival_quantity - orderdetail.inferior_quantity
                if not plan_quantity:
                    continue
                arrival_quantity_delta = min(plan_quantity, inbound_sku_dict['arrival_quantity'])
                inferior_quantity_delta = min(plan_quantity, inbound_sku_dict['inferior_quantity'])

                if arrival_quantity_delta:
                    inbound_sku_dict['arrival_quantity'] -= arrival_quantity_delta
                    orderdetail.arrival_quantity += arrival_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL % {'id': orderdetail.id, 'msg': '更新 到货数+%d' % arrival_quantity_delta})

                if inferior_quantity_delta:
                    inbound_sku_dict['inferior_quantity'] -= inferior_quantity_delta
                    orderdetail.inferior_quantity += inferior_quantity_delta
                    orderdetail.save()
                    op_logs.append(self.ORDERDETAIL_OP_LOG_TPL % {'id': orderdetail.id, 'msg': '更新 次品数+%d' % inferior_quantity_delta})

                if arrival_quantity_delta or inferior_quantity_delta:
                    inbound_record = OrderDetailInBoundDetail(
                        orderdetail=orderdetail,
                        inbounddetail=inbound_detail,
                        arrival_quantity=arrival_quantity_delta,
                        inferior_quantity=inferior_quantity_delta)
                    inbound_record.save()
                    msg = '创建 订货明细ID:%d 入库明细ID:%d 到货数:+%d 次品数:+%d' % (orderdetail.id, inbound_detail.id, arrival_quantity_delta, inferior_quantity_delta)
                    op_logs.append(self.ORDERDETAIL_INBOUNDDETAIL_OP_LOG_TPL % {'id': inbound_record.id, 'msg': msg})
                if not (inbound_sku_dict.get('arrival_quantity') or
                        inbound_sku_dict.get('inferior_quantity')):
                    inbound_skus_dict.pop(sku_id, False)
        if len_of_op_logs == len(op_logs):
            op_logs.append('执行完毕, 无需重新分配')
        return Response({'msg': ''.join(map(lambda x: '<p>%s</p>' % x, op_logs))})


    @list_route(methods=['post'])
    def create_supplier_inbound(self, request):
        form = forms.EditInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'error': '参数错误'})

        inbound_skus_dict = json.loads(form.cleaned_attrs.skus)
        if not inbound_skus_dict:
            return Response({'error': '请填写入库数据'})
        inbound_skus_dict = {int(k): v
                             for k, v in inbound_skus_dict.iteritems()}

        supplier_id = form.cleaned_attrs.target_id

        old_skus_dict = {}
        dinghuo_stats = OrderDetail.objects.filter(orderlist__supplier_id=supplier_id) \
              .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
              .values('product_id', 'chichu_id') \
              .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            _, sku_id = map(int, (s['product_id'], s['chichu_id']))
            old_skus_dict[sku_id] = {
                'buy_quantity': s['buy_quantity'],
                'arrival_quantity': s['arrival_quantity'],
                'inferior_quantity': s['inferior_quantity'],
                'plan_quantity': s['buy_quantity'] - s['arrival_quantity'] -
                s['inferior_quantity']
            }

        error_skus_dict = {}
        for sku_id, inbound_sku_dict in inbound_skus_dict.iteritems():
            plan_quantity = (old_skus_dict.get(sku_id) or
                             {}).get('plan_quantity') or 0
            in_quantity = inbound_sku_dict[
                'arrival_quantity'] + inbound_sku_dict['inferior_quantity']
            if plan_quantity < in_quantity:
                error_skus_dict[sku_id] = {
                    'plan_quantity': plan_quantity,
                    'error': '大于待入库数'
                }
        if error_skus_dict:
            return Response({'error': '入库异常', 'error_skus': error_skus_dict})

        inbound = InBound(supplier_id=supplier_id,
                          sent_from=InBound.SUPPLIER,
                          creator=request.user)
        if form.cleaned_attrs.express_no:
            inbound.express_no = form.cleaned_attrs.express_no
        inbound.save()

        skus_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            skus_dict[sku.id] = {
                'product_id': sku.product.id,
                'sku_id': sku.id,
                'outer_id': sku.product.outer_id,
                'product_name': sku.product.name,
                'properties_name': sku.properties_name or
                sku.properties_alias or '',
                'quantity': sku.quantity
            }

        inbound_details = {}
        for sku_id, inbound_sku_dict in inbound_skus_dict.iteritems():
            sku_dict = skus_dict.get(sku_id)
            if not sku_dict:
                continue
            product_id = sku_dict['product_id']
            outer_id = sku_dict['outer_id']
            product_name = sku_dict['product_name']
            properties_name = sku_dict['properties_name']
            arrival_quantity = inbound_sku_dict['arrival_quantity']
            inferior_quantity = inbound_sku_dict['inferior_quantity']

            inbound_sku_dict.update({
                'outer_id': outer_id,
                'product_name': product_name,
                'properties_name': properties_name
            })

            inbound_detail = InBoundDetail(inbound=inbound,
                                           product_id=product_id,
                                           sku_id=sku_id,
                                           product_name=product_name,
                                           outer_id=outer_id,
                                           properties_name=properties_name,
                                           arrival_quantity=arrival_quantity,
                                           inferior_quantity=inferior_quantity)
            inbound_detail.save()
            inbound_details[sku_id] = inbound_detail

        orderlists_with_express_no = []
        orderlists_without_express_no = []
        for orderlist in OrderList.objects.filter(supplier_id=form.cleaned_attrs.target_id) \
          .exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]).order_by('created'):
            if form.cleaned_attrs.express_no and orderlist.express_no:
                if form.cleaned_attrs.express_no.strip() in \
                    self.EXPRESS_NO_SPLIT_PATTERN.split(orderlist.express_no.strip()):
                    orderlists_with_express_no.append(orderlist)
                    continue
            orderlists_without_express_no.append(orderlist)

        orderlists = orderlists_with_express_no + orderlists_without_express_no
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                inbound_detail = inbound_details.get(sku_id)
                if not (inbound_detail and inbound_sku_dict):
                    continue
                plan_quantity = orderdetail.buy_quantity - orderdetail.arrival_quantity - orderdetail.inferior_quantity
                if not plan_quantity:
                    continue
                arrival_quantity_delta = min(
                    plan_quantity, inbound_sku_dict['arrival_quantity'])
                inferior_quantity_delta = min(
                    plan_quantity, inbound_sku_dict['inferior_quantity'])

                if arrival_quantity_delta:
                    inbound_sku_dict[
                        'arrival_quantity'] -= arrival_quantity_delta
                    orderdetail.arrival_quantity += arrival_quantity_delta
                    orderdetail.save()

                if inferior_quantity_delta:
                    inbound_sku_dict[
                        'inferior_quantity'] -= inferior_quantity_delta
                    orderdetail.inferior_quantity += inferior_quantity_delta
                    orderdetail.save()

                if arrival_quantity_delta or inferior_quantity_delta:
                    inbound_record = OrderDetailInBoundDetail(
                        orderdetail=orderdetail,
                        inbounddetail=inbound_detail,
                        arrival_quantity=arrival_quantity_delta,
                        inferior_quantity=inferior_quantity_delta)
                    inbound_record.save()

                if not (inbound_sku_dict.get('arrival_quantity') or
                        inbound_sku_dict.get('inferior_quantity')):
                    inbound_skus_dict.pop(sku_id, False)

        return Response({'inbound_id': inbound.id})

    @list_route(methods=['get'])
    def list_for_inbound(self, request):
        data = []
        error = None

        def _refund_data(refund_id):
            pass

        def _inbound_data(inbound_id):
            pass

        def _supplier_data(supplier_id):
            sku_ids = set()
            products_dict = {}

            dinghuo_stats = OrderDetail.objects.filter(orderlist__supplier_id=supplier_id) \
              .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
              .values('product_id', 'chichu_id') \
              .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
            for s in dinghuo_stats:
                product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
                sku_ids.add(sku_id)

                skus_dict = products_dict.setdefault(product_id, {})
                skus_dict[sku_id] = {
                    'id': sku_id,
                    'buy_quantity': s['buy_quantity'],
                    'arrival_quantity': s['arrival_quantity'],
                    'inferior_quantity': s['inferior_quantity'],
                    'plan_quantity': s['buy_quantity'] - s['arrival_quantity'] -
                    s['inferior_quantity']
                }

            new_products_dict = {}
            for sku in ProductSku.objects.select_related('product').filter(
                    id__in=list(sku_ids)):
                product_id = sku.product.id
                sku_id = sku.id

                product_dict = new_products_dict.setdefault(
                    product_id, {'id': product_id,
                                 'name': sku.product.name,
                                 'outer_id': sku.product.outer_id,
                                 'pic_path': '%s?imageView2/0/w/120' %
                                 sku.product.pic_path.strip(),
                                 'skus': {}})
                sku_dict = products_dict[product_id][sku_id]
                sku_dict.update({
                    'properties_name': sku.properties_name or
                    sku.properties_alias,
                    'quantity': sku.quantity
                })
                product_dict['skus'][sku_id] = sku_dict

            data = []
            for product_id in sorted(new_products_dict.keys()):
                product_dict = new_products_dict[product_id]
                product_dict['skus'] = [
                    product_dict['skus'][k]
                    for k in sorted(product_dict['skus'].keys())
                ]
                data.append(product_dict)
            return data

        supplier_dict = {}
        express_no_dict = {}
        for orderlist in OrderList.objects.select_related('supplier').exclude(
                status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]):
            if not orderlist.supplier_id:
                continue
            if orderlist.supplier_id not in supplier_dict:
                supplier_dict[
                    orderlist.supplier_id] = orderlist.supplier.supplier_name
            if orderlist.express_no:
                for express_no in self.EXPRESS_NO_SPLIT_PATTERN.split(
                        orderlist.express_no.strip()):
                    express_no_dict[express_no.strip()] = orderlist.supplier_id

        form = forms.InBoundListForm(request.GET)
        if not form.is_valid():
            error = '输入有错误'
        else:
            if form.cleaned_attrs.sent_from == InBound.SUPPLIER:
                supplier_id = None
                if form.cleaned_attrs.target_id:
                    supplier_id = form.cleaned_attrs.target_id
                else:
                    if form.cleaned_attrs.supplier:
                        for sid, supplier_name in supplier_dict.iteritems():
                            if supplier_name.strip(
                            ) == form.cleaned_attrs.supplier:
                                supplier_id = sid
                                break
                if not supplier_id:
                    error = '找不到供应商'
                else:
                    data = _supplier_data(supplier_id)
            elif form.sent_from == InBound.REFUND:
                pass

        result = {
            'suppliers': [{'id': k,
                           'text': supplier_dict[k]}
                          for k in sorted(supplier_dict.keys())],
            'express_nos': [{'id': express_no_dict[k],
                             'text': k,
                             'sent_from': InBound.SUPPLIER}
                            for k in sorted(express_no_dict.keys())],
            'data': data
        }
        result.update(form.json)
        return Response(result, template_name='dinghuo/inbound.html')
