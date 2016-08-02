# coding=utf-8
__author__ = 'yan.huang'
from .models.message import XlmmMessage
from .serializers import XlmmMessageSerializers
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import generics, viewsets, permissions, authentication, renderers
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route, list_route
from core.utils.modelutils import get_class_fields


class XlmmMessageViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin):
    """
    - {prefix}/method: `get`  获取用户的投诉列表
    - {prefix}/method: `post` 创建用户的投诉条目　　
        -  com_type     类型 :   `0`: 购物问题;
                                `1`: 订单相关;
                                `2`: 意见/建议;
                                `4`: 售后问题;
                                `3`: 其他
        -  com_title    标题 default 问题反馈
        -  com_content  内容
        -  contact_way  联系方式
    - reply method: `post`  回复
    """
    queryset = XlmmMessage.objects.filter(dest=None)
    serializer_class = XlmmMessageSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def self_list(self, request):
        try:
            mama = request.admin.customer.get_getXiaolumm()
        except:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        queryset = XlmmMessage.get_msg_list(mama.id,)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['GET', 'POST'])
    def read(self, request, pk):
        try:
            mama = request.admin.customer.get_getXiaolumm()
        except:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        message = get_object_or_404(XlmmMessage, pk=pk)
        if message.mama != mama:
            raise exceptions.ValidationError(u'无法修改')