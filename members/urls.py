from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='member_dashboard'),
    path('stock/', views.stock, name='member_stock'),
    path('log-consumption/', views.consumption, name='member_consumption'),
    path('log-consumption/save/', views.consumption_log, name='member_consumption_log'),
    path('alerts/', views.alerts, name='member_alerts'),
    path('shopping-list/', views.shopping, name='member_shopping'),
    path('complaints/', views.complaints, name='member_complaints'),
    path('feedback/', views.feedback, name='member_feedback'),
    path('profile/', views.profile, name='member_profile'),
]
