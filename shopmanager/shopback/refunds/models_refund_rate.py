# coding=utf-8
"""
退款率模型, 数据计算方法
"""
from django.db import models


class PayRefundRate(models.Model):
    """"
    任务执行生成数据 每天定时运行 将过去15天内的特卖订单退款率数据写入数据库中
    """
    date_cal = models.DateField(db_index=True, unique=True, verbose_name=u'结算日期')  # 唯一
    ref_num = models.IntegerField(default=0, verbose_name=u'退款单数')
    pay_num = models.IntegerField(default=0, verbose_name=u'付款单数')
    ref_rate = models.FloatField(default=0.0, verbose_name=u'退款率')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'flashsale_pay_refundrate'
        verbose_name = u'特卖/退款率表'
        verbose_name_plural = u'特卖/退款率列表'

    def __unicode__(self):
        return u"%s" % self.date_cal