from django.conf.urls import url, include

from django.contrib.auth import views as authviews

from . import views

app_name = 'attendance'
urlpatterns = [
    # Display latest games in curernt quarter. ex: /attendance/
    url(r'^transactions/$', views.TransactionsView.as_view(), name='transactions'),
    url(r'^password_change/$', authviews.password_change, {'post_change_redirect': 'attendance:password_change_done'}, name='password_change'),
    url(r'^password_reset/$', authviews.password_reset, {'post_reset_redirect': 'attendance:password_reset_done'}, name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        authviews.password_reset_confirm, {'post_reset_redirect': 'attendance:password_reset_complete'}, name='password_reset_confirm'),
    url('^', include('django.contrib.auth.urls')),
]
