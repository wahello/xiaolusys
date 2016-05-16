# -*- encoding:utf-8 -*-

from django.db.models import F
from django.db import IntegrityError
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import ReferalRelationship, GroupRelationship, UniqueVisitor
from flashsale.pay.models_user import Customer
from flashsale.xiaolumm.models import XiaoluMama

import sys


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_update_referal_relationship(sale_order):
    sale_trade = sale_order.sale_trade
    customer_id = sale_trade.buyer_id
    customer = Customer.objects.get(pk=customer_id)

    mamas = XiaoluMama.objects.filter(openid=customer.unionid)
    if mamas.count() <= 0:
        return

    # mama status is taken care of by some other logic, so we ignore.
    # mamas.update(status=XiaoluMama.EFFECT, progress=XiaoluMama.PAY, charge_status=XiaoluMama.CHARGED)
    to_mama_id = mamas[0].id

    extra = sale_trade.extras_info
    mm_linkid = 0
    if 'mm_linkid' in extra:
        mm_linkid = int(extra['mm_linkid'] or '0')

    if mm_linkid <= 0:
        return

    logger.warn("%s: mm_linkid=%s, to_mama_id=%s" % (get_cur_info(), mm_linkid, to_mama_id))

    records = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id)
    if records.count() <= 0:
        record = ReferalRelationship(referal_from_mama_id=mm_linkid,
                                     referal_to_mama_id=to_mama_id,
                                     referal_to_mama_nick=customer.nick,
                                     referal_to_mama_img=customer.thumbnail)
        record.save()


@task()
def task_update_group_relationship(leader_mama_id, referal_relationship):
    print "%s, mama_id: %s" % (get_cur_info(), referal_relationship.referal_from_mama_id)

    records = GroupRelationship.objects.filter(member_mama_id=referal_relationship.referal_to_mama_id)
    if records.count() <= 0:
        record = GroupRelationship(leader_mama_id=leader_mama_id,
                                   referal_from_mama_id=referal_relationship.referal_from_mama_id,
                                   member_mama_id=referal_relationship.referal_to_mama_id,
                                   member_mama_nick=referal_relationship.referal_to_mama_nick,
                                   member_mama_img=referal_relationship.referal_to_mama_img)

        record.save()


from flashsale.xiaolumm.util_unikey import gen_uniquevisitor_unikey
from shopapp.weixin.options import get_unionid_by_openid


@task()
def task_update_unique_visitor(mama_id, openid, appkey, click_time):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    if XiaoluMama.objects.filter(pk=mama_id).count() <= 0:
        return

    nick, img = '', ''
    unionid = get_unionid_by_openid(openid, appkey)
    if unionid:
        customers = Customer.objects.filter(unionid=unionid)
        if customers.count() > 0:
            nick, img = customers[0].nick, customers[0].thumbnail
    else:
        # if no unionid exists, then use openid
        unionid = openid

    date_field = click_time.date()
    uni_key = gen_uniquevisitor_unikey(openid, date_field)

    try:
        visitor = UniqueVisitor(mama_id=mama_id, visitor_unionid=unionid, visitor_nick=nick,
                                visitor_img=img, uni_key=uni_key, date_field=date_field)
        visitor.save()
    except IntegrityError:
        logger.warn("IntegrityError - UniqueVisitor | mama_id: %s, uni_key: %s" % (mama_id, uni_key))
        pass
        # visitor already visited a mama's link, ignoring.


from flashsale.promotion.models_freesample import AppDownloadRecord
from flashsale.xiaolumm.models_fans import XlmmFans
from flashsale.xiaolumm.models import XiaoluMama


@task()
def task_login_activate_appdownloadrecord(user):
    customers = Customer.objects.filter(user=user)
    if not customers.exists():
        return

    customer = customers[0]
    self_mama = customer.getXiaolumm()
    if self_mama:
        # XiaoluMama can't be a fan of any others.
        return
    
    unionid = customer.unionid
    mobile = customer.mobile

    records = None
    if unionid:
        records = AppDownloadRecord.objects.filter(unionid=unionid, status=AppDownloadRecord.UNUSE).order_by('-created')
        record = records.first()
        if record:
            record.status = AppDownloadRecord.USED
            record.save()
            logger.warn("task_login_activate_appdownloadrecord|customer_id:%s, record_id:%s" % (customer.id, record.id))
            return
    
    if mobile and len(mobile) == 11:
        records = AppDownloadRecord.objects.filter(mobile=mobile, status=AppDownloadRecord.UNUSE).order_by('-created')
        record = records.first()
        if record:
            record.status = AppDownloadRecord.USED
            record.save()
            logger.warn("task_login_activate_appdownloadrecord|customer_id:%s, record_id:%s" % (customer.id, record.id))

    
 
@task()
def task_login_create_appdownloadrecord(user):
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return

    fan = XlmmFans.objects.filter(fans_cusid=customer.id).first()
    if not fan:
        return

    mobile = customer.mobile
    if len(mobile) != 11:
        return

    mobile_customer = Customer.objects.filter(mobile=mobile,unionid='').first()
    if not mobile_customer:
        return

    from_customer = fan.xlmm_cusid
    record = AppDownloadRecord(from_customer=from_customer,status=AppDownloadRecord.USED,mobile=mobile)
    record.save()
    

    
    

    
