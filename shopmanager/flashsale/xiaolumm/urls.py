from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required  
from django.views.generic import TemplateView

from . import views ,views_duokefu,views_top100_iter,mama_data_search
from .views_register import MamaRegisterView,MamaConfirmView


urlpatterns = patterns('',
    url(r'^$',views.landing),
    url(r'^m/$',views.MamaStatsView.as_view(),name="mama_homepage"),
    url(r'^register/(?P<mama_id>\d+)/$',MamaRegisterView.as_view(),name="mama_register"),
    url(r'^register/confirm/$',MamaConfirmView.as_view(),name="mama_confirm"),
    url(r'^help/sharewx/$', TemplateView.as_view(template_name="mama_sharewx.html"), name='mama_sharewx'),
    url(r'^help/recruit/$', TemplateView.as_view(template_name="mama_recruit.html"), name='mama_recruit'),
    url(r'^income/$',views.MamaIncomeDetailView.as_view()),
    
    url(r'^stats/$',staff_member_required(views.StatsView.as_view())),
    url(r'^cashout/$',views.CashoutView.as_view()),
    url(r'^cashoutlist/$',views.CashOutList.as_view()),
    url(r'^carrylist/$',views.CarryLogList.as_view()),
    url(r'^(?P<linkid>\d+)/$',views.logclicks),    
    url(r'^charge/(?P<pk>\d+)/$',staff_member_required(views.chargeWXUser)),
    url(r'^xlmm/(?P<pk>\d+)/$', staff_member_required(views.XiaoluMamaModelView.as_view())),
    url(r'^cashoutverify/(?P<xlmm>\d+)/(?P<id>\d+)/$',staff_member_required(views.cash_Out_Verify),name="cashout_verify"),
    url(r'^cashmodify/(?P<data>\w+)/$',staff_member_required(views.cash_modify)), #
    url(r'^cashreject/(?P<data>\w+)/$',staff_member_required(views.cash_reject)), #
    url(r'^stats_summary/$',staff_member_required(views.stats_summary),name="stats_summary"),
    url(r'^mama_verify/(?P<id>\d+)/$',staff_member_required(views.mama_Verify),name="mama_verify"),
    url(r'^mama_verify_action/$',staff_member_required(views.mama_Verify_Action),name="mama_verify_action"),

    url(r'^duokefu_customer/$',views_duokefu.kf_Customer,name="kf_Customer"),
    url(r'^duokefu_search/$',views_duokefu.kf_Search_Page,name="kf_Search_Page"),
    url(r'^duokefu_search_by_mobile/$',views_duokefu.kf_Search_Order_By_Mobile,name="search_Order_By_Mobile"),
    url(r'^duokefu_weixin_order/$',views_duokefu.kf_Weixin_Order,name="weixin_Order"),
    url(r'^duokefu_order_detail/$',views_duokefu.kf_Search_Order_Detail,name="kf_Search_Order_Detail"),
    url(r'^duokefu_find_more/$',views_duokefu.ke_Find_More_Weixin_Order,name="ke_Find_More_Weixin_Order"),
    #url(r'^duokefu_logistics/$',views_duokefu.kf_Logistics,name="kf_Logistics"),
    
    url(r'^top50/click/$', views.xlmm_Click_Top, name="xlmm_Click_Top"),
    url(r'^top50/order/$',views.xlmm_Order_Top,name="xlmm_Order_Top"),
    url(r'^top50/conversion/$',views.xlmm_Conversion_Top, name="xlmm_Conversion_Top"),

    url(r'^top50/click/week/$', views.xlmm_Click_Top_Week, name="xlmm_Click_Top_Week"),
    url(r'^top50/order/week/$', views.xlmm_Order_Top_Week, name="xlmm_Order_Top_Week"),

    url(r'^top50/click/month/$', views.xlmm_Click_Top_Month, name="xlmm_Click_Top_Month"),
    url(r'^top50/order/month/$', views.xlmm_Order_Top_Month, name="xlmm_Order_Top_Month"),
    url(r'^top50/convers/month/$', views.xlmm_Convers_Top_Month, name="xlmm_Convers_Top_Month"),
    #xlmm_TOP50_By_Manager_Month
    url(r'^top50/order_manager/month/', staff_member_required(views.xlmm_TOP50_By_Manager_Month), name="xlmm_TOP50_By_Manager_Month"),

    # ITER TOP100
    url(r'^top100/click/month/$', views_top100_iter.Top100_Click, name="Top100_Click"),
    url(r'^top100/order/month/$', views_top100_iter.Top100_Order, name="Top100_Click"),

    # mama data search
    url(r'^mama_show_all/$', staff_member_required(mama_data_search.all_Show), name="MamaAll"),

)
