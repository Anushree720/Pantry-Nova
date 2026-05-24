from django.urls import path
from . import views


urlpatterns = [
    path('', views.landing, name='landing'),

    path('register/manager/', views.manager_register, name='manager_register'),
    path('register/member/', views.member_register, name='member_register'),

    path('login/manager/', views.manager_login, name='manager_login'),
    path('login/member/', views.member_login, name='member_login'),
    path('login/admin/', views.admin_login, name='admin_login'),

    path('logout/', views.logout_view, name='logout'),

    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/new/', views.password_reset_new, name='password_reset_new'),
    path('password-reset/resend/', views.password_reset_resend, name='password_reset_resend'),
]
