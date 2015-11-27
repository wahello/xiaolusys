# -*- coding:utf-8 -*-
from django.db import models


class ClickCount(models.Model):
    
    linkid = models.IntegerField(db_index=True,verbose_name=u'链接ID')
    weikefu = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'微客服')
    agencylevel = models.IntegerField(default=1, verbose_name=u"类别")
    mobile = models.CharField(max_length=11, verbose_name=u"手机")
    
    user_num = models.IntegerField(default=0, verbose_name=u'人数')
    valid_num = models.IntegerField(default=0, verbose_name=u'有效点击人数')
    click_num = models.IntegerField(default=0, verbose_name=u'次数')
    date = models.DateField(db_index=True,verbose_name=u'日期')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')
    username = models.IntegerField(default=0, db_index=True, verbose_name=u'接管人')

    class Meta:
        db_table = 'flashsale_clickcount'
        unique_together = ('linkid', 'date')  # 联合索引
        app_label = 'xiaolumm'
        verbose_name = u'点击统计表'
        verbose_name_plural = u'点击统计表列表'
        ordering=['-date']
        permissions = [('browser_xlmm_active', u'浏览代理活跃度')]

    def __unicode__(self):
        return self.weikefu


class WeekCount(models.Model):
    
    linkid = models.IntegerField(db_index=True,verbose_name=u'链接ID')
    weikefu = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'微客服')
    user_num = models.IntegerField(default=0, verbose_name=u'点击人数')
    valid_num = models.IntegerField(default=0, verbose_name=u'有效点击数')
    buyercount = models.IntegerField(default=0, verbose_name=u'购买人数')
    ordernumcount = models.IntegerField(default=0, verbose_name=u'订单总数')
    conversion_rate = models.FloatField(default=0, verbose_name=u'转化率')
    week_code = models.CharField(max_length=6, verbose_name=u'周编码')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')

    class Meta:
        db_table = "flashsale_weekcount_table"
        unique_together = ('linkid', 'week_code')  # 联合索引
        app_label = 'xiaolumm'
        verbose_name = u"代理转化率周统计"
        verbose_name_plural = u"代理转化率周统计列表"
        ordering = ['write_time']
        
    def __unicode__(self):
        return self.weikefu


from django.db.models.signals import post_save
from flashsale.clickcount.tasks import task_Count_ClickCount_Info
from flashsale.xiaolumm.models import Clicks

# def Create_Or_Change_Clickcount(sender, instance, created, **kwargs):
#     task_Count_ClickCount_Info.s(instance, created)()
# #     task_Count_ClickCount_Info(instance, created)
# 
# post_save.connect(Create_Or_Change_Clickcount, sender=Clicks)


