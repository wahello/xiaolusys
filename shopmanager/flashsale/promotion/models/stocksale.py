# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.db.models import F, Sum
from core.models import BaseModel, AdminModel
from shopback.trades.models import Product
from supplychain.supplier.models import SaleProduct
from flashsale.promotion.models import ActivityEntry
from shopback.items.models import ProductSkuStats


class BatchStockSale(AdminModel):
    STATUS_CHOICES = ((0, u'初始'), (1, u'数据完成'), (2, u'关闭'))
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name=u'状态')
    total = models.IntegerField(default=0, verbose_name=u'选品总数')
    product_total = models.IntegerField(default=0, verbose_name=u'商品总数')
    sku_total = models.IntegerField(default=0, verbose_name=u'SKU总数')
    stock_total = models.IntegerField(default=0, verbose_name=u'可售库存总数')
    expected_time = models.DateField(null=True, blank=True, verbose_name=u'期望日期')

    class Meta:
        db_table = 'flashsale_stocksale_batch'
        app_label = 'promotion'
        verbose_name = u'最后疯抢活动批次'
        verbose_name_plural = u'最后疯抢活动批次列表'

    @staticmethod
    def gen(user):
        batch = BatchStockSale(creator=user)
        batch.save()
        return batch

    def get_expected_time(self):
        if not self.expected_time:
            t = self.created + datetime.timedelta(days=1)
            return datetime.datetime(t.year, t.month, t.day)
        return self.expected_time

    @staticmethod
    def get_next_batch_id():
        obj = BatchStockSale.objects.order_by('-id').first()
        return obj.id if obj else 1


class ActivityStockSale(AdminModel):
    """专题 最后疯抢"""
    activity = models.ForeignKey(ActivityEntry, null=True, verbose_name=u'专题活动')
    # batch_num = models.IntegerField(default=0, verbose_name=u'批次序号')
    batch = models.ForeignKey(BatchStockSale, verbose_name=u'批次号')
    day_batch_num = models.IntegerField(default=0, verbose_name=u'专题序号')
    onshelf_time = models.DateField(verbose_name=u'上架日期')
    offshelf_time = models.DateField(verbose_name=u'下架日期')
    total = models.IntegerField(default=0, verbose_name=u'选品总数')
    product_total = models.IntegerField(default=0, verbose_name=u'商品总数')
    sku_total = models.IntegerField(default=0, verbose_name=u'SKU总数')
    stock_total = models.IntegerField(default=0, verbose_name=u'可售库存总数')

    class Meta:
        db_table = 'flashsale_stocksale_activity'
        app_label = 'promotion'
        verbose_name = u'最后疯抢活动专题'
        verbose_name_plural = u'最后疯抢活动专题列表'

    @staticmethod
    def get_begin_time():
        last_activity = ActivityStockSale.objects.filter().order_by('-id').first()
        if not last_activity:
            last_batch = BatchStockSale.objects.filter().order_by('-id').first()
            return last_batch.get_expected_time()
        return last_activity.offshelf_time


class StockSale(AdminModel):
    sale_product = models.ForeignKey(SaleProduct, null=True)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(verbose_name=u'当前库存数')
    sku_num = models.IntegerField(default=0, verbose_name=u'包含sku种数')
    batch = models.ForeignKey(BatchStockSale, verbose_name=u'批次号')
    day_batch_num = models.IntegerField(default=0, verbose_name=u'专题序号')
    # expected_time = models.DateField(null=True, verbose_name=u'日期')
    activity = models.ForeignKey(ActivityStockSale, null=True)
    STATUS_CHOICES = ((0, u'初始'), (1, u'在线'), (2, u'关闭'))
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name=u'状态')
    stock_safe = models.IntegerField(choices=((0, u'未确认'), (1, u'已确认'), (2, u'无须确认')), default=0, verbose_name=u'库存状态')
    INTERVAL = 2

    class Meta:
        db_table = 'flashsale_stocksale'
        app_label = 'promotion'
        verbose_name = u'库存倾销商品'
        verbose_name_plural = u'库存倾销商品列表'

    @staticmethod
    def get_max_day_batch_num(batch_num):
        obj = ActivityStockSale.objects.filter(batch_id=batch_num).order_by('-id').first()
        return obj.day_batch_num if obj else 0

    @staticmethod
    def gen_new_stock_sale(user):
        """获取"""
        if BatchStockSale.objects.filter(status__in=[0, 1]).exists():
            raise Exception(u'此前的批次尚未处理完，请先关闭此前的批次')
        batch = BatchStockSale.gen(user)
        res = {}
        for stat in ProductSkuStats.get_auto_sale_stock().select_related('product'):
            if stat.product_id not in res:
                res[stat.product_id] = StockSale(
                    sale_product_id=stat.product.sale_product if stat.product.sale_product else None,
                    product=stat.product,
                    batch=batch,
                    day_batch_num=0,
                    quantity=stat.realtime_quantity,
                    sku_num=1
                )
            else:
                res[stat.product_id].quantity += stat.realtime_quantity
                res[stat.product_id].sku_num += 1
        StockSale.objects.bulk_create(res.values())
        product_ids = res.keys()
        batch.status = 1
        batch.sku_total = ProductSkuStats.get_auto_sale_stock().filter(product_id__in=product_ids).count()
        batch.stock_total = ProductSkuStats.get_auto_sale_stock().filter(product_id__in=product_ids).aggregate(
            s=Sum(F('history_quantity') + F('inbound_quantity') + F('adjust_quantity') + F('return_quantity')
                  - F('post_num')) - F('rg_quantity')).get('s', 0)
        batch.product_total = len(product_ids)
        batch.total = len(batch.stocksale_set.exclude(sale_product=None).values('sale_product_id').distinct())
        batch.save()
        return batch

    @staticmethod
    def gen_new_activity(cnt=100):
        """
            获取100个sale_order, 生成新活动。时间为最后次专题活动时间或批次生成时间
        """
        batch_id = BatchStockSale.objects.order_by('-id').first().id
        old_day_batch_num = StockSale.get_max_day_batch_num(batch_id)
        new_day_batch_num = old_day_batch_num + 1
        new_expected_time = ActivityStockSale.get_begin_time()
        sale_product_ids = [s['sale_product_id'] for s in
                            StockSale.objects.filter(batch_id=batch_id, day_batch_num=0).values(
                                'sale_product_id').distinct()[0:cnt]]
        product_total = StockSale.objects.filter(sale_product_id__in=sale_product_ids,
                                                 batch_id=batch_id).count()
        product_ids = [s['product_id'] for s in StockSale.objects.filter(sale_product_id__in=sale_product_ids,
                                                                         batch_id=batch_id).values('product_id')]
        sku_total = ProductSkuStats.get_auto_sale_stock().filter(product_id__in=product_ids).count()
        # self.history_quantity + self.inbound_quantity + self.adjust_quantity + self.return_quantity - self.post_num - self.rg_quantity
        stock_total = ProductSkuStats.get_auto_sale_stock().filter(product_id__in=product_ids).aggregate(
            s=Sum(F('history_quantity') + F('inbound_quantity') + F('adjust_quantity') + F('return_quantity')
                  - F('post_num')) - F('rg_quantity')).get('s', 0)
        ass = ActivityStockSale(batch_id=batch_id,
                                day_batch_num=new_day_batch_num,
                                onshelf_time=new_expected_time,
                                offshelf_time=new_expected_time + datetime.timedelta(days=StockSale.INTERVAL),
                                total=len(sale_product_ids),
                                product_total=product_total,
                                sku_total=sku_total,
                                stock_total=stock_total
                                )
        ass.save()
        StockSale.objects.filter(sale_product_id__in=sale_product_ids,
                                 batch_id=batch_id, day_batch_num=0).update(
            day_batch_num=new_day_batch_num,
            activity=ass
        )
        return ass.id

    def get_xiaolumama_(self):
        return

    def set_product_price(self):
        return

    @staticmethod
    def get_sale_product_to_sale_cnt():
        product_ids = [p['product_id'] for p in ProductSkuStats.get_auto_sale_stock().values('product_id').distinct()]
        return len(Product.objects.filter(id__in=product_ids).values('sale_product').distinct())
