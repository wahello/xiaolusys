# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-01 16:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daystats', '0004_add_sku_amount_and_delivery_stat'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailystat',
            name='total_coin',
            field=models.IntegerField(default=0, verbose_name='\u5c0f\u9e7f\u5e01\u652f\u4ed8\u989d'),
        ),
        migrations.AlterField(
            model_name='dailyskuamountstat',
            name='model_id',
            field=models.IntegerField(db_index=True, default=0, verbose_name='\u6b3e\u5f0fID'),
        ),
        migrations.AlterField(
            model_name='dailyskudeliverystat',
            name='model_id',
            field=models.IntegerField(db_index=True, default=0, verbose_name='\u6b3e\u5f0fID'),
        ),
        migrations.AlterField(
            model_name='dailystat',
            name='total_coupon',
            field=models.IntegerField(default=0, verbose_name='\u5238\u652f\u4ed8\u989d'),
        ),
    ]