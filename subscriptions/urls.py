from django.urls import path
from . import views


urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('manager/billing/', views.billing, name='manager_billing'),
    path('manager/billing/checkout/<slug:slug>/', views.checkout, name='subs_checkout'),
    path('manager/billing/pay/<slug:slug>/', views.process_payment, name='subs_pay'),
    path('manager/billing/success/<int:payment_id>/', views.payment_success, name='subs_success'),
    path('manager/billing/cancel/', views.cancel_subscription, name='subs_cancel'),
    path('manager/billing/invoice/<int:payment_id>/', views.invoice, name='subs_invoice'),
]
