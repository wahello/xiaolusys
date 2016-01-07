from django.conf.urls.defaults import patterns, include, url
from shopback.categorys.views import crawFullCategories, getCategoryIds, getCategoryTree
from views_stats import CategoryStatViewSet

urlpatterns = patterns('',
                       url(r'^update/(?P<cid>[^/]+)/$', crawFullCategories, name='update_categories'),
                       url(r'^cats_by_name/$', getCategoryIds, name='get_cats_by_name'),
                       url(r'^cats_tree/$', getCategoryTree, name='get_cats_tree'),
                       url(r'^cate_stat/$', CategoryStatViewSet.as_view(), name='get_stat_data')
                       )
