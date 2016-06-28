# -*- encoding:utf8 -*-
import json
from django.conf import settings
from django.db import IntegrityError, models
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import View

import logging
logger = logging.getLogger(__name__)

from flashsale.pay import tasks

import pingpp

class PINGPPCallbackView(View):
    def post(self, request, *args, **kwargs):

        content = request.body
        logger.debug('pingpp callback:%s' % content)
        try:
            # 读取异步通知数据
            notify = json.loads(content)
        except:
            return HttpResponse('no params')

        response = ''
        # 对异步通知做处理
        if 'object' not in notify:
            response = 'fail'
        else:
            if notify['object'] == 'charge':
                # 开发者在此处加入对支付异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradePayTask(notify)
                else:
                    tasks.notifyTradePayTask.delay(notify)

                response = 'success'
            elif notify['object'] == 'refund':
                # 开发者在此处加入对退款异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradeRefundTask(notify)
                else:
                    tasks.notifyTradeRefundTask.delay(notify)

                response = 'success'
            else:
                response = 'fail'

        return HttpResponse(response)

    get = post


########## alipay callback ###########
class PayResultView(View):
    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        logger.info('pay result:%s' % content)

        return HttpResponseRedirect(reverse('user_orderlist'))


class WXPayWarnView(View):
    def post(self, request, *args, **kwargs):
        content = request.body
        logger.error('wx warning:%s' % content)
        return HttpResponse('ok')

    get = post