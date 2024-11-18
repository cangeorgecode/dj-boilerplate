from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/logged_out/', views.custom_logout, name='logged_out'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    path('create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('subscribe/', views.subscribe, name='subscribe'), 
    path('', views.index, name='index'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe-webhook'),
    path('change-password/', views.change_password, name='change_password'),
    path('change-password/done/', views.password_change_done, name='password_change_done'),
    path('billing-portal/', views.stripe_billing_portal, name='stripe_billing_portal'),
    path('receipt/', views.receipt, name='receipt'),
    path('upgrade-subscription/', views.upgrade_subscription, name='upgrade_subscription'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('check_username/', views.check_username, name='check_username'),
]
