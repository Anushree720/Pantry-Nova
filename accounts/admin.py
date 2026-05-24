from django.contrib import admin
from .models import Login, PasswordResetOTP

admin.site.register(Login)
admin.site.register(PasswordResetOTP)
