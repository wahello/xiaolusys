# coding=utf-8
import logging
import datetime
from celery.task import task
from django.db.models import F
from flashsale.xiaolumm.models import XiaoluMama

logger = logging.getLogger(__name__)


@task()
def task_update_tpl_released_coupon_nums(template):
    """
    template : CouponTemplate instance
    has_released_count ++ when the CouponTemplate release success.
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(template_id=template.id).count()
    template.has_released_count = count
    template.save(update_fields=['has_released_count'])
    return


@task()
def task_update_share_coupon_release_count(share_coupon):
    """
    share_coupon : OrderShareCoupon instance
    release_count ++ when the OrderShareCoupon release success
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(order_coupon_id=share_coupon.id).count()
    share_coupon.release_count = count
    share_coupon.save(update_fields=['release_count'])
    return


@task()
def task_update_coupon_use_count(coupon, trade_tid):
    """
    1. count the CouponTemplate 'has_used_count' field when use coupon
    2. count the OrderShareCoupon 'has_used_count' field when use coupon
    """
    from flashsale.coupon.models import UserCoupon

    coupon.finished_time = datetime.datetime.now()  # save the finished time
    coupon.trade_tid = trade_tid  # save the trade tid with trade be binding
    coupon.save(update_fields=['finished_time', 'trade_tid'])
    tpl = coupon.self_template()

    coupons = UserCoupon.objects.all()
    tpl_used_count = coupons.filter(template_id=tpl.id, status=UserCoupon.USED).count()
    tpl.has_used_count = tpl_used_count
    tpl.save(update_fields=['has_used_count'])

    share = coupon.share_record()
    if share:
        share_used_count = coupons.filter(order_coupon_id=share.id, status=UserCoupon.USED).count()
        share.has_used_count = share_used_count
        share.save(update_fields=['has_used_count'])
    return


@task()
def task_release_coupon_for_order(saletrade):
    """
    - SaleTrade pay confirm single to drive this task.
    """
    from flashsale.coupon.models import CouponTemplate, UserCoupon

    extras_info = saletrade.extras_info
    ufrom = extras_info.get('ufrom')
    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_ORDER_BENEFIT).first()
    if not tpl:
        return
    UserCoupon.objects.create_mama_invite_coupon(
        buyer_id=saletrade.buyer_id,
        template_id=tpl.id,
        trade_id=saletrade.id,
        ufrom=ufrom,
    )
    return


@task()
def task_freeze_coupon_by_refund(salerefund):
    """
    - SaleRefund refund signal to drive this task.
    """
    from flashsale.coupon.models import UserCoupon

    trade_tid = salerefund.get_tid()
    cous = UserCoupon.objects.filter(trade_tid=trade_tid,
                                     status=UserCoupon.UNUSED)
    if cous.exists():
        cous.update(status=UserCoupon.FREEZE)


@task()
def task_release_mama_link_coupon(saletrade):
    """
    - SaleTrade pay confirm single to drive this task
    - when a customer buy a trade with the mama link url then release a coupon for that mama.
    """
    extras_info = saletrade.extras_info
    mama_id = extras_info.get('mm_linkid') or None
    ufrom = extras_info.get('ufrom')

    order = saletrade.sale_orders.all().first()
    if order and order.item_id in ['22030', '14362', '2731']:  # spacial product id
        return

    if not mama_id:
        return
    mama = XiaoluMama.objects.filter(id=mama_id, charge_status=XiaoluMama.CHARGED).first()
    if not mama:
        return
    customer = mama.get_mama_customer()
    if not customer:
        return
    from flashsale.coupon.models import CouponTemplate, UserCoupon

    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_MAMA_INVITE).first()
    if not tpl:
        return
    UserCoupon.objects.create_mama_invite_coupon(
        buyer_id=customer.id,
        template_id=tpl.id,
        trade_id=saletrade.id,
        ufrom=ufrom,
    )
    return


@task()
def task_change_coupon_status_used(saletrade):
    coupon_id = saletrade.extras_info.get('coupon') or None
    from flashsale.coupon.models import UserCoupon

    usercoupon = UserCoupon.objects.filter(id=coupon_id,
                                           customer_id=saletrade.buyer_id,
                                           status=UserCoupon.UNUSED
                                           ).first()
    if not usercoupon:
        return
    usercoupon.use_coupon(saletrade.tid)


@task()
def task_update_user_coupon_status_2_past():
    """
    - timing to update the user coupon to past.
    """
    from flashsale.coupon.models import UserCoupon

    today = datetime.datetime.today()
    cous = UserCoupon.objects.filter(
        expires_time__lte=today,
        status__in=[UserCoupon.UNUSED, UserCoupon.FREEZE]
    )
    cous.update(status=UserCoupon.PAST)  # 更新为过期优惠券


@task()
def task_release_coupon_for_register(instance):
    """
     - release coupon for register a new Customer instance ( when post save created a Customer instance run this task)
    """
    from flashsale.pay.models_user import Customer

    if not isinstance(instance, Customer):
        return
    from flashsale.coupon.models import UserCoupon

    tpl_ids = [54, 55, 56, 57, 58, 59, 60]
    for tpl_id in tpl_ids:
        try:
            UserCoupon.objects.create_normal_coupon(
                buyer_id=instance.id,
                template_id=tpl_id,
            )
        except:
            logger.error(u'task_release_coupon_for_register for customer id %s' % instance.id)
            continue
    return


@task()
def task_roll_back_usercoupon_by_refund(trade_tid):
    from flashsale.coupon.models import UserCoupon
    cou = UserCoupon.objects.filter(trade_tid=trade_tid).first()
    if cou:
        cou.release_usercoupon()
    return


@task()
def task_update_mobile_download_record(tempcoupon):
    from flashsale.coupon.models import OrderShareCoupon
    share = OrderShareCoupon.objects.filter(uniq_id=tempcoupon.share_coupon_id).first()
    if not share:
        return
    from flashsale.promotion.models_freesample import DownloadMobileRecord

    dl_record = DownloadMobileRecord.objects.filter(from_customer=share.share_customer,
                                                    mobile=tempcoupon.mobile).first()
    if dl_record:  # 记录存在不做处理
        return
    dl_record = DownloadMobileRecord(
        from_customer=share.share_customer,
        mobile=tempcoupon.mobile,
        ufrom=DownloadMobileRecord.REDENVELOPE,
        uni_key='/'.join([str(share.share_customer), str(tempcoupon.mobile)]))
    dl_record.save()


@task()
def task_update_unionid_download_record(usercoupon):
    from flashsale.promotion.models_freesample import DownloadUnionidRecord, DownloadMobileRecord
    customer = usercoupon.customer
    if not customer.unionid.strip():  # 没有unionid  写mobilde 记录
        dl_record = DownloadMobileRecord.objects.filter(from_customer=usercoupon.share_user_id,
                                                        mobile=customer.mobile).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadMobileRecord(
            from_customer=usercoupon.share_user_id,
            mobile=customer.mobile,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            uni_key='/'.join([str(usercoupon.share_user_id), str(customer.mobile)]))
        dl_record.save()
    else:
        dl_record = DownloadUnionidRecord.objects.filter(from_customer=usercoupon.share_user_id,
                                                         unionid=customer.unionid).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadUnionidRecord(
            from_customer=usercoupon.share_user_id,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            unionid=customer.unionid,
            uni_key='/'.join([str(usercoupon.share_user_id), str(customer.unionid)]),
            headimgurl=customer.thumbnail,
            nick=customer.nick
        )
        dl_record.save()
