# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-22 10:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0022_product_ref_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='SkuWareStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ware_by', models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (4, '\u8702\u5de2\u82cf\u5dde\u4ed3'), (5, '\u8702\u5de2\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93')),
                ('psi_paid_num', models.IntegerField(default=0, verbose_name='\u5f85\u5904\u7406\u6570')),
                ('psi_prepare_book_num', models.IntegerField(default=0, verbose_name='\u5f85\u8ba2\u8d27\u6570')),
                ('psi_booked_num', models.IntegerField(default=0, verbose_name='\u5df2\u8ba2\u8d27\u6570')),
                ('psi_ready_num', models.IntegerField(default=0, verbose_name='\u5f85\u5206\u914d\u6570')),
                ('psi_third_send_num', models.IntegerField(default=0, verbose_name='\u5f85\u4f9b\u5e94\u5546\u53d1\u8d27\u6570')),
                ('psi_assigned_num', models.IntegerField(default=0, verbose_name='\u5f85\u5408\u5355\u6570')),
                ('psi_merged_num', models.IntegerField(default=0, verbose_name='\u5f85\u6253\u5355\u6570')),
                ('psi_waitscan_num', models.IntegerField(default=0, verbose_name='\u5f85\u626b\u63cf\u6570')),
                ('psi_waitpost_num', models.IntegerField(default=0, verbose_name='\u5f85\u79f0\u91cd\u6570')),
                ('psi_sent_num', models.IntegerField(default=0, verbose_name='\u5f85\u7b7e\u6536\u6570')),
                ('psi_finish_num', models.IntegerField(default=0, verbose_name='\u5b8c\u6210\u6570')),
                ('adjust_quantity', models.IntegerField(default=0, verbose_name='\u8c03\u6574\u6570')),
                ('history_quantity', models.IntegerField(default=0, verbose_name='\u5386\u53f2\u5e93\u5b58\u6570')),
                ('inbound_quantity', models.IntegerField(default=0, verbose_name='\u5165\u4ed3\u5e93\u5b58\u6570')),
                ('return_quantity', models.IntegerField(default=0, verbose_name='\u5ba2\u6237\u9000\u8d27\u6570')),
                ('rg_quantity', models.IntegerField(default=0, verbose_name='\u9000\u8fd8\u4f9b\u5e94\u5546\u8d27\u6570')),
                ('assign_num', models.IntegerField(default=0, verbose_name='\u5df2\u5206\u914d\u6570')),
                ('post_num', models.IntegerField(default=0, verbose_name='\u5df2\u53d1\u8d27\u6570')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('modified', models.DateTimeField(auto_now=True, null=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('status', models.IntegerField(choices=[(0, 'EFFECT'), (1, 'DISCARD')], db_index=True, default=0, verbose_name='\u72b6\u6001')),
            ],
            options={
                'db_table': 'shop_items_ware_stock',
                'verbose_name': 'SKU\u5e93\u5b58',
                'verbose_name_plural': 'SKU\u5e93\u5b58\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='inferiorskustats',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (4, '\u8702\u5de2\u82cf\u5dde\u4ed3'), (5, '\u8702\u5de2\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
        migrations.AlterField(
            model_name='product',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (4, '\u8702\u5de2\u82cf\u5dde\u4ed3'), (5, '\u8702\u5de2\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
        migrations.AddField(
            model_name='skuwarestock',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='items.Product', verbose_name='\u5546\u54c1'),
        ),
        migrations.AddField(
            model_name='skuwarestock',
            name='sku',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='items.ProductSku', verbose_name='SKU'),
        ),
    ]