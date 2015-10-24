# coding=utf-8
"""
代理广告处理
"""
from django.db import models


class XlmmAdvertis(models.Model):
    INNER_LEVEL = 1
    VIP_LEVEL = 2
    A_LEVEL = 3

    PEOPLE_CHOICE = ((INNER_LEVEL, u'内部级别'), (VIP_LEVEL, u'VIP代理'), (A_LEVEL, u'A类代理'))

    title = models.CharField(max_length=64, db_index=True, verbose_name=u'广告标题')
    cntnt = models.TextField(max_length=512, verbose_name=u'广告内容')
    show_people = models.IntegerField(choices=PEOPLE_CHOICE, verbose_name=u"展示对象")
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')
    is_valid = models.BooleanField(default=False, verbose_name=u"是否投放")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'flashsale_xlmm_advertis'
        verbose_name = u'代理广告表'
        verbose_name_plural = u'代理广告表列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)
