# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('shopapp.second_time_sort.views',
    url(r'^batch_number/$','batch_number'),
    url(r'^batch_pick/$','batch_pick'),
#    url(r'^start_exam/$','start_exam'),
#    url(r'^write_select_paper/$','write_select_paper'),
#    url(r'^correct_problem_count/$','correct_problem_count'),

)


