# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categorys', '0003_add_productcategory_created_and_modified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productcategory',
            name='grade',
            field=models.IntegerField(db_index=True, default=0, verbose_name='\u7c7b\u76ee\u7ea7\u522b'),
        ),
    ]