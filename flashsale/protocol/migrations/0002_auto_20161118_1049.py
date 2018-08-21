# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('protocol', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appfullpushmessge',
            name='platform',
            field=models.CharField(choices=[(b'all', b'\xe5\x85\xa8\xe9\x83\xa8\xe7\x94\xa8\xe6\x88\xb7'), (b'ios', b'\xe5\x85\xa8\xe9\x83\xa8IOS\xe7\x94\xa8\xe6\x88\xb7'), (b'android', b'\xe5\x85\xa8\xe9\x83\xa8ANDROID\xe7\x94\xa8\xe6\x88\xb7'), (b'xlmm', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88'), (b'xlmm_A', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88\xef\xbc\xa1\xe7\xb1\xbb'), (b'xlmm_VIP1', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88VIP1'), (b'xlmm_VIP2', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88VIP2'), (b'xlmm_VIP4', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88VIP4'), (b'xlmm_VIP6', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88VIP6'), (b'xlmm_VIP8', b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88VIP8'), (b'customer_pay', b'\xe8\xb4\xad\xe4\xb9\xb0\xe8\xbf\x87\xe7\x9a\x84\xe7\x94\xa8\xe6\x88\xb7'), (b'CESHI', b'\xe5\x86\x85\xe9\x83\xa8\xe6\xb5\x8b\xe8\xaf\x95\xe4\xb8\x93\xe7\x94\xa8')], db_index=True, max_length=16, verbose_name='\u5e73\u53f0'),
        ),
        migrations.AlterField(
            model_name='appfullpushmessge',
            name='status',
            field=models.SmallIntegerField(choices=[(-1, '\u7b49\u5f85\u63a8\u9001'), (0, '\u63a8\u9001\u5931\u8d25'), (1, '\u63a8\u9001\u6210\u529f')], db_index=True, default=-1, verbose_name='\u72b6\u6001'),
        ),
        migrations.AlterField(
            model_name='appfullpushmessge',
            name='target_url',
            field=models.IntegerField(choices=[(1, b'\xe4\xbb\x8a\xe6\x97\xa5\xe4\xb8\x8a\xe6\x96\xb0'), (2, b'\xe6\x98\xa8\xe6\x97\xa5\xe7\x89\xb9\xe5\x8d\x96'), (3, b'\xe6\xbd\xae\xe7\xab\xa5\xe4\xb8\x93\xe5\x8c\xba'), (4, b'\xe6\x97\xb6\xe5\xb0\x9a\xe5\xa5\xb3\xe8\xa3\x85'), (5, b'\xe5\x95\x86\xe5\x93\x81\xe8\xaf\xa6\xe6\x83\x85'), (8, b'\xe4\xbc\x98\xe6\x83\xa0\xe5\x88\xb8'), (10, b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88/\xe9\xa6\x96\xe9\xa1\xb5'), (11, b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88/\xe6\xaf\x8f\xe6\x97\xa5\xe6\x8e\xa8\xe9\x80\x81'), (9, b'webView\xe7\xbd\x91\xe9\xa1\xb5'), (13, b'\xe5\xb0\x8f\xe9\xb9\xbf\xe8\xae\xba\xe5\x9d\x9b'), (15, b'\xe6\xb4\xbb\xe5\x8a\xa8\xe7\x95\x8c\xe9\x9d\xa2'), (16, b'\xe5\x88\x86\xe7\xb1\xbb\xe5\x95\x86\xe5\x93\x81')], default=1, verbose_name=b'\xe8\xb7\xb3\xe8\xbd\xac\xe9\xa1\xb5\xe9\x9d\xa2'),
        ),
    ]