# coding=utf-8
import datetime
import random

from core.managers import BaseManager
from flashsale.coupon import tasks


def check_template(template_id):
    """ 优惠券检查 没有问题则返回优惠券 """
    from flashsale.coupon.models import CouponTemplate

    try:
        tpl = CouponTemplate.objects.get(id=int(template_id))  # 获取优惠券模板
        try:
            tpl.template_valid_check()  # 有效性检查
            tpl.check_date()  # 时间检查
        except Exception, exc:
            return None, 6, exc.message  # 不在模板定义的发放时间内
        else:
            return tpl, 0, u'优惠券正常'  # 没有抛出异常则返回tpl
    except CouponTemplate.DoesNotExist:
        return None, 5, u"没有发放"


def check_target_user(buyer_id, tpl):
    """ 身份判定（判断身份是否和优惠券模板指定用户一致） 注意　这里是硬编码　和　XiaoluMama　代理级别关联"""
    from flashsale.coupon.models import CouponTemplate

    user_level = CouponTemplate.TARGET_ALL
    from flashsale.pay.models import Customer

    customer = Customer.objects.get(id=int(buyer_id))
    if tpl.target_user != CouponTemplate.TARGET_ALL:  # 如果不是所有用户可领取则判定级别
        xlmm = customer.getXiaolumm()
        if xlmm:
            user_level = xlmm.agencylevel  # 用户的是代理身份 内1 　VIP 2  A 3

    if user_level != tpl.target_user:
        # 如果用户领取的优惠券和用户身份不一致则不予领取
        return None, 4, u"用户不一致"
    return customer, 0, u'客户身份一致'


def check_template_release_nums(tpl, template_id):
    """ 优惠券发放数量检查 """
    from flashsale.coupon.models import UserCoupon

    coupons = UserCoupon.objects.filter(template_id=int(template_id))
    tpl_release_count = coupons.count()  # 当前模板的优惠券条数
    if tpl_release_count > tpl.prepare_release_num:  # 如果大于定义的限制领取数量
        return None, 3, u"优惠券已经发完了"
    return coupons, 0, u"优惠券有存量"


def calculate_value_and_time(tpl):
    """
    计算发放优惠券价值和开始使用时间和结束时间
    """
    value = tpl.value  # 默认取模板默认值
    if tpl.is_random_val and tpl.min_val and tpl.max_val:  # 如果设置了随机值则选取随机值
        value = float('%.1f' % random.uniform(tpl.max_val, tpl.min_val))  # 生成随机的value

    expires_time = tpl.use_deadline
    start_use_time = datetime.datetime.now()
    if tpl.is_flextime:  # 如果是弹性时间
        # 断言设置弹性时间的时候 仅仅设置一个 定制日期  否则报错
        AssertionError(tpl.limit_after_release_days == 0 or tpl.use_after_release_days == 0)
        if tpl.limit_after_release_days:  # 发放后多少天内可用 days 使用时间即 领取时间 过期时间为领取时间+ days
            expires_time = start_use_time + datetime.timedelta(days=tpl.limit_after_release_days)
        if tpl.use_after_release_days:  # 发放多少天后可用 即开始时间 为 模板开始发放的时间+use_after_release_days
            start_use_time = start_use_time + datetime.timedelta(days=tpl.use_after_release_days)
            expires_time = tpl.use_deadline
        AssertionError(start_use_time < expires_time)  # 断言开始时间 < 结束时间

    return value, start_use_time, expires_time


def make_uniq_id(tpl, customer_id, trade_id=None, share_id=None, refund_id=None):
    """
    生成 uniq_id: template.id + template.coupon_type + customer_id +
    """
    from flashsale.coupon.models import CouponTemplate

    uniqs = [str(tpl.id), str(tpl.coupon_type), str(customer_id)]
    if tpl.coupon_type == CouponTemplate.TYPE_NORMAL:  # 普通类型 1
        uniqs = uniqs

    elif tpl.coupon_type == CouponTemplate.TYPE_ORDER_BENEFIT and trade_id:  # 下单红包 2
        uniqs.append(str(trade_id))

    elif tpl.coupon_type == CouponTemplate.TYPE_ORDER_SHARE and share_id:  # 订单分享 3
        uniqs.append(str(share_id))

    elif tpl.coupon_type == CouponTemplate.TYPE_MAMA_INVITE and trade_id:  # 推荐专享 4
        uniqs.append(str(trade_id))  # 一个专属链接可以有多个订单

    elif tpl.coupon_type == CouponTemplate.TYPE_COMPENSATE and refund_id:  # 售后补偿 5
        uniqs.append(str(refund_id))
    else:
        raise Exception('Template type is tpl.coupon_type : %s !' % tpl.coupon_type)
    return '_'.join(uniqs)


class UserCouponManager(BaseManager):
    def create_normal_coupon(self, buyer_id, template_id, ufrom=None, **kwargs):
        """
        创建普通类型优惠券
        这里不计算领取数量(默认只能领取一张 不填写 uniq_id的张数内容)
        """
        from flashsale.coupon.models import UserCoupon, CouponTemplate

        ufrom = ufrom or ''
        if not (buyer_id and template_id):
            return None, 7, u'没有发放'

        tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
        if not tpl:  # 没有找到模板或者没有
            return tpl, code, tpl_msg
        AssertionError(tpl.coupon_type == CouponTemplate.TYPE_NORMAL)  # 模板类型不是 普通类型 则抛出异常
        customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
        if not customer:  # 用户不存在
            return customer, code, cu_msg

        coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
        if coupons is None:  # coupons 该优惠券的发放queryset
            return coupons, code, tpl_n_msg

        value, start_use_time, expires_time = calculate_value_and_time(tpl)

        # 唯一键约束 是: template_id_customer_id_order_coupon_id_(number_of_tpl)  一个模板 多次分享 不同的分享id 不同的用户
        uniq_id = make_uniq_id(tpl, customer.id)
        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=int(buyer_id),
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        return cou, 0, u"领取成功"

    def create_mama_invite_coupon(self, buyer_id, template_id, trade_id=None, ufrom=None, **kwargs):
        """
        创建代理链接购买优惠券
        """
        from flashsale.coupon.models import UserCoupon, CouponTemplate

        ufrom = ufrom or ''
        trade_id = trade_id or ''
        if not (buyer_id and template_id and trade_id):
            return None, 7, u'没有发放'
        tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
        if not tpl:  # 没有找到模板或者没有
            return tpl, code, tpl_msg
        AssertionError(tpl.coupon_type == CouponTemplate.TYPE_MAMA_INVITE)  # 模板类型不是 推荐专享 则抛出异常
        customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
        if not customer:  # 用户不存在
            return customer, code, cu_msg

        coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
        if coupons is None:  # coupons 该优惠券的发放queryset
            return coupons, code, tpl_n_msg

        value, start_use_time, expires_time = calculate_value_and_time(tpl)
        # 唯一键约束 是: template_id_customer_id_order_coupon_id_(number_of_tpl)  一个模板 多次分享 不同的分享id 不同的用户
        uniq_id = make_uniq_id(tpl, customer.id, trade_id=trade_id)
        print ('-------------------------')
        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        print(extras)
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=int(buyer_id),
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        return cou, 0, u"领取成功"

    def create_order_finish_coupon(self, buyer_id, template_id, trade_id=None, ufrom=None, **kwargs):
        """
        创建下单优惠券
        """
        from flashsale.coupon.models import UserCoupon, CouponTemplate

        ufrom = ufrom or ''
        trade_id = trade_id or ''
        if not (buyer_id and template_id and trade_id):
            return None, 7, u'没有发放'
        tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
        if not tpl:  # 没有找到模板或者没有
            return tpl, code, tpl_msg
        AssertionError(tpl.coupon_type == CouponTemplate.TYPE_ORDER_BENEFIT)  # 模板类型不是 下单红包 则抛出异常
        customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
        if not customer:  # 用户不存在
            return customer, code, cu_msg

        coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
        if coupons is None:  # coupons 该优惠券的发放queryset
            return coupons, code, tpl_n_msg

        value, start_use_time, expires_time = calculate_value_and_time(tpl)
        # 唯一键约束 是: template_id_customer_id_order_coupon_id_(number_of_tpl)  一个模板 多次分享 不同的分享id 不同的用户
        uniq_id = make_uniq_id(tpl, customer.id, trade_id=trade_id)
        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=int(buyer_id),
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        return cou, 0, u"领取成功"

    def create_refund_post_coupon(self, buyer_id, template_id, refund_id=None, ufrom=None, **kwargs):
        """
        创建退货补贴邮费优惠券
        这里计算领取数量(默认能领取多张 填写 uniq_id的张数内容)
        """
        from flashsale.coupon.models import UserCoupon, CouponTemplate

        ufrom = ufrom or ''
        refund_id = refund_id or ''
        if not (buyer_id and template_id and refund_id):
            return None, 7, u'没有发放'
        tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
        if not tpl:  # 没有找到模板或者没有
            return tpl, code, tpl_msg
        AssertionError(tpl.coupon_type == CouponTemplate.TYPE_COMPENSATE)  # 模板类型不是 售后补偿 则抛出异常
        customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
        if not customer:  # 用户不存在
            return customer, code, cu_msg

        coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
        if coupons is None:  # coupons 该优惠券的发放queryset
            return coupons, code, tpl_n_msg

        value, start_use_time, expires_time = calculate_value_and_time(tpl)
        # 唯一键约束 是: template_id_customer_id_order_coupon_id_(number_of_tpl)  一个模板 多次分享 不同的分享id 不同的用户
        uniq_id = make_uniq_id(tpl, customer.id, refund_id=refund_id)
        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=int(buyer_id),
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        return cou, 0, u"领取成功"

    def create_order_share_coupon(self, buyer_id, template_id, share_uniq_id=None, ufrom=None, **kwargs):
        """
        创建订单分享优惠券
        # 如果是分享类型 判断批次领取
        """
        from flashsale.coupon.models import UserCoupon, CouponTemplate, OrderShareCoupon

        ufrom = ufrom or ''
        share_uniq_id = share_uniq_id or ''
        if not (buyer_id and template_id):
            return None, 7, u'没有发放'
        share_coupon = OrderShareCoupon.objects.filter(uniq_id=share_uniq_id).first()
        if not share_coupon:  # 如果分享类型没有uniq_id号码则不予领取优惠券
            return None, 1, u"没有领取到呢"

        tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
        if not tpl:  # 没有找到模板或者没有
            return tpl, code, tpl_msg

        AssertionError(tpl.coupon_type == CouponTemplate.TYPE_ORDER_SHARE)  # 模板类型不是订单分享类型则抛出异常
        customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
        if not customer:
            return customer, code, cu_msg

        coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
        if coupons is None:
            return coupons, code, tpl_n_msg

        user_coupons = coupons.filter(customer_id=int(buyer_id))

        batch_coupon = user_coupons.filter(order_coupon_id=share_coupon.id).first()
        if batch_coupon:  # 如果该批次号已经领取过了 则返回优惠券(订单分享的订单仅能领取一个优惠券)
            return user_coupons, 0, u'已经领取'
        if not share_coupon.release_count < share_coupon.limit_share_count:  # 该批次的领取
            return user_coupons, 0, u'该分享已领完'

        value, start_use_time, expires_time = calculate_value_and_time(tpl)

        # 唯一键约束 是: template_id_customer_id_order_coupon_id_(number_of_tpl)  一个模板 多次分享 不同的分享id 不同的用户
        uniq_id = make_uniq_id(tpl, customer.id, share_id=share_coupon.id)

        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        cou = UserCoupon.objects.create(template_id=int(template_id),
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=int(buyer_id),
                                        share_user_id=share_coupon.share_customer,
                                        order_coupon_id=share_coupon.id,
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        # update the share_coupon.release_count
        tasks.task_update_share_coupon_release_count.delay(share_coupon)
        return cou, 0, u"领取成功"
