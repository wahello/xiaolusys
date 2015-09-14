# coding:utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product, ProductSku, ProductSkuContrast, ContrastContent
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from flashsale.pay.models_custom import ModelProduct, Productdetail
from django.db import transaction
from supplychain.supplier.models import SaleSupplier
from shopback.base import log_action, ADDITION, CHANGE


class AddItemView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "items/add_item.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({"v": "v"})

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        content = request.data
        user = request.user

        product_name = content.get("product_name", "")
        category = content.get("category", "")
        shelf_time = content.get("shelf_time", "")
        material = content.get("material", "")
        note = content.get("note", "")
        wash_instroduce = content.get("wash_instroduce", "")
        header_img = content.get("header_img", "")
        ware_by = content.get("ware_by", "")
        supplier = content.get("supplier", "")
        if product_name == "" or category == "" or wash_instroduce == "" \
                or shelf_time == "" or material == "" or supplier == ""\
                or header_img == "" or ware_by == "":
            return Response({"result": "填写表单错误"})
        category_item = ProductCategory.objects.get(cid=category)
        if category_item.parent_cid == 5:
            first_outer_id = u"9"
        elif category_item.parent_cid == 8:
            first_outer_id = u"8"
        else:
            return Response({"result": "类别错误"})
        outer_id = first_outer_id + str(category_item.cid) + "%05d" % int(supplier)
        count = 1
        while True:
            inner_outer_id = outer_id + "%03d" % count
            test_pro = Product.objects.filter(outer_id=(inner_outer_id + "1"))
            if test_pro.count() == 0:
                break
            count += 1
        if len(inner_outer_id) > 12:
            return Response({"result": "编码生成错误"})
        print "product_name:", product_name
        print "category:", category
        print "outer_id:", inner_outer_id
        print "material:", material
        print "note:", note
        print "wash_instroduce:", wash_instroduce
        print "header_img", header_img
        print "shelf_time:", shelf_time
        print "ware_by:", ware_by
        print "supplier", "%05d" % int(supplier)
        # return Response({"result": "temp"})
        model_pro = ModelProduct(name=product_name, head_imgs=header_img, sale_time=shelf_time)
        model_pro.save()
        log_action(user.id, model_pro, ADDITION, u'新建一个modelproduct new')
        all_colors = content.get("all_colors", "").split(",")
        all_sku = content.get("all_sku", "").split(",")
        all_chi_ma = content.get("all_chima", "").split(",")
        chi_ma_result = {}
        for sku in all_sku:
            for chi_ma in all_chi_ma:
                temp_chi_ma = ContrastContent.objects.get(name=chi_ma)
                if sku in chi_ma_result:
                    chi_ma_result[sku][temp_chi_ma.id] = content.get(sku + "_" + chi_ma + "_size")
                else:
                    chi_ma_result[sku] = {temp_chi_ma.id: content.get(sku + "_" + chi_ma + "_size")}
        pro_count = 1
        for color in all_colors:
            total_remain_num = 0

            for sku in all_sku:
                remain_num = content.get(color + "_" + sku + "_remainnum", "")
                cost = content.get(color + "_" + sku + "_cost", "")
                price = content.get(color + "_" + sku + "_pricestd", "")
                agentprice = content.get(color + "_" + sku + "_agentprice", "")
                total_remain_num += int(remain_num)

            one_product = Product(name=product_name + "/" + color, outer_id=inner_outer_id + str(pro_count),
                                  model_id=model_pro.id, sale_charger=user.username,
                                  category=category_item, remain_num=total_remain_num, cost=cost,
                                  agent_price=agentprice, std_sale_price=price, ware_by=int(ware_by),
                                  sale_time=shelf_time, pic_path=header_img)
            one_product.save()
            log_action(user.id, one_product, ADDITION, u'新建一个product_new')
            pro_count += 1
            one_product_detail = Productdetail(product=one_product, material=material,
                                               color=content.get("all_colors", ""),
                                               wash_instructions=wash_instroduce, note=note)
            one_product_detail.save()
            log_action(user.id, one_product, ADDITION, u'新建一个detail_new')
            chima_model = ProductSkuContrast(product=one_product, contrast_detail=chi_ma_result)
            chima_model.save()
            count = 1
            for sku in all_sku:
                remain_num = content.get(color + "_" + sku + "_remainnum", "")
                cost = content.get(color + "_" + sku + "_cost", "")
                price = content.get(color + "_" + sku + "_pricestd", "")
                agentprice = content.get(color + "_" + sku + "_agentprice", "")
                one_sku = ProductSku(outer_id=count, product=one_product, remain_num=remain_num, cost=cost,
                                     std_sale_price=price, agent_price=agentprice, properties_alias=sku)
                one_sku.save()
                log_action(user.id, one_product, ADDITION, u'新建一个sku_new')
                count += 1
        return Response({"result": "OK", "outer_id": inner_outer_id})


class GetCategory(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.filter(status=ProductCategory.NORMAL)
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result_data = {}

        root_category = self.queryset.filter(parent_cid=0)
        temp = {}
        for category in root_category:
            temp[category.cid] = category.name
            child_category = self.queryset.filter(parent_cid=category.cid)
            child_temp = {}
            for c_category in child_category:
                child_temp[c_category.cid] = c_category.name
                third_child_category = self.queryset.filter(parent_cid=c_category.cid)
                third_temp = {}
                for t_category in third_child_category:
                    third_temp[t_category.cid] = t_category.name
                if third_child_category.count() > 0:
                    result_data["0," + str(category.cid) + "," + str(c_category.cid)] = third_temp
            result_data["0," + str(category.cid)] = child_temp
        result_data['0'] = temp
        return Response(result_data)


class GetSupplier(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.filter(status=SaleSupplier.CHARGED)
    renderer_classes = (JSONRenderer,)

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result_data = {}
        supplier_id = request.GET.get("supplier_id", "0")
        all_supplier = self.queryset
        if supplier_id != "0":
            all_supplier = all_supplier.filter(id=supplier_id)
        for supplier in all_supplier:
            result_data[supplier.id] = supplier.supplier_name
        return Response({"0": result_data})


class GetSkuDetail(generics.ListCreateAPIView):
    queryset = ProductSkuContrast.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        result_data = {}
        # product_id = "14036"
        # a = Product.objects.get(id=14036)
        # s = ProductSku.objects.get(id=54392)
        # all_sku = self.queryset.filter(product_id=product_id)
        # print all_sku[0].contrast_detail[s.properties_alias], type(all_sku[0].contrast_detail)
        #
        # if all_sku.count() > 0:
        #     return Response({"result": all_sku[0].contrast_detail})
        return Response({"0": result_data})