"""URL configuration for flashcards app"""
from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('upgrade/', views.upgrade, name='upgrade'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('subscription/<int:subscription_id>/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/<int:subscription_id>/renew/', views.renew_subscription, name='renew_subscription'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('webhook/payment/', views.payment_webhook, name='payment_webhook'),
    path('upload/', views.upload_file, name='upload_file'),
    path('set/<int:set_id>/', views.view_flashcards, name='view_flashcards'),
    path('set/<int:set_id>/test/', views.start_test, name='start_test'),
    path('set/<int:set_id>/submit/', views.submit_test, name='submit_test'),
    path('results/<int:session_id>/', views.test_results, name='test_results'),
]

