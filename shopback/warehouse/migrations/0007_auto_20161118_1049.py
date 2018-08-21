# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0006_stock_adjust_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockadjust',
            name='status',
            field=models.IntegerField(blank=True, choices=[(0, '\u521d\u59cb'), (1, '\u5df2\u5904\u7406'), (-1, '\u5df2\u4f5c\u5e9f')], default=0),
        ),
        migrations.AlterField(
            model_name='stockadjust',
            name='ware_by',
            field=models.IntegerField(blank=True, choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=0, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
    ]