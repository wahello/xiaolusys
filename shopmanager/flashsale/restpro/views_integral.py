# coding=utf-8

from rest_framework import viewsets
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from rest_framework.response import Response

from flashsale.pay.models_coupon import IntegralLog, Integral


class UserIntegralViewSet(viewsets.ModelViewSet):
    queryset = Integral.objects.all()
    serializer_class = serializers.UserIntegralSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserIntegralLogViewSet(viewsets.ModelViewSet):
    queryset = IntegralLog.objects.all()
    serializer_class = serializers.UserIntegralLogSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        # 过滤已经确定的积分
        queryset = queryset.filter(log_status=IntegralLog.CONFIRM)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)