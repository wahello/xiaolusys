from django.conf.urls.defaults import patterns, include, url



urlpatterns = patterns('',

    (r'^taobao/rank/','search.views.getShopsRank'),
    (r'^rank/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.genPeriodChart'),

    (r'^keys/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.genItemKeywordsRankChart'),
    (r'^rank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.genPageRankPivotChart'),

    (r'^trade/periodchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.getTradePeroidChart'),
    (r'^trade/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.getTradePivotChart'),

    (r'^avgrank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','search.views.genItemAvgRankPivotChart'),
    (r'^ordernum/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','shopback.orders.views.genHourlyOrdersChart'),

)


  