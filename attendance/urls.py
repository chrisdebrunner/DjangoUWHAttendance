from django.urls import path, include
from django.contrib.auth import views as authviews
from . import views

app_name = 'attendance'
urlpatterns = [
    # Display transactions for current quarter. ex: /attendance/
    path('transactions/', views.TransactionsView.as_view(), name='transactions'),
    path('password_change/', authviews.PasswordChangeView.as_view(success_url='/attendance/password_change/done/'), name='password_change'),
    path('password_change/done/', authviews.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', authviews.PasswordResetView.as_view(success_url='/attendance/password_reset/done/'), name='password_reset'),
    path('password_reset/done/', authviews.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', authviews.PasswordResetConfirmView.as_view(success_url='/attendance/reset/complete/'), name='password_reset_confirm'),
    path('reset/complete/', authviews.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', include('django.contrib.auth.urls')),
]
