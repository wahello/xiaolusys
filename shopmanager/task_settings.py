import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = "djkombu.transport.DatabaseTransport"

EXECUTE_INTERVAL_TIME = 5*60

EXECUTE_RANGE_TIME = 3*60

UPDATE_ITEM_NUM_INTERVAL = 2*60

UPDATE_UNPAY_ORDER_INTERVAL = 3*60

GET_TAOBAO_DATA_PAGE_SIZE = 200 #the page_size of  per request

PRODUCT_TRADE_RANK_BELOW = 10

from celery.schedules import crontab


CELERYBEAT_SCHEDULE = {
    'runs-every-10-minutes':{
        'task':'shopback.task.tasks.updateAllItemListTask',
        'schedule':crontab(minute='*/5'),
        'args':(),
    },
    'runs-every-day-a':{
        'task':'shopback.items.tasks.updateAllItemNumTask',
        'schedule':crontab(minute="0",hour="0"),
        'args':(),
    },
    'runs-every-day-b':{
        'task':'subway.tasks.deleteHotkeyAndLiftValueTask',
        'schedule':crontab(minute="30",hour="0"),
        'args':(),
    },
    'runs-every-30-minutes_a':{
        'task':'search.tasks.updateItemKeywordsPageRank',
        'schedule':crontab(minute="0,30",hour=','.join([str(i) for i in range(7,24)])),
        'args':()
    },
    'runs-every-hours':{
        'task':'shopback.orders.tasks.updateAllUserHourlyOrders',
        'schedule':crontab(minute="0",hour="*/1"),
        'args':()
    },
#    'runs-every-day_b':{
#        'task':'search.tasks.updateProductTradeBySellerTask',
#        'schedule':crontab(minute="0",hour="1"),
#        'args':()
#    },
    'runs-every-day_c':{
        'task':'search.tasks.deletePageRankRecordTask',
        'schedule':crontab(minute="0",hour="1"),
        'args':(30,)
    },
}


