from django.conf.urls import url

from . import views

app_name = 'attendance'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /attendance/5/
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # ex: /attendance/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /attendance/5/vote/
    url(r'^(?P<game_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
