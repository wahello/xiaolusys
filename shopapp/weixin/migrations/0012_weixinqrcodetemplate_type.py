# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-01 20:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0011_add_account_name_to_weixinaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='weixinqrcodetemplate',
            name='type',
            field=models.IntegerField(choices=[(0, '\u5206\u4eab\u9080\u8bf7\u6a21\u677f'), (1, '\u4ee3\u7406\u6388\u6743\u6a21\u677f')], db_index=True, default=0, verbose_name='\u6a21\u677f\u7c7b\u578b'),
        ),
    ]