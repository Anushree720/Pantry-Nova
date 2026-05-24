from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Login(models.Model):
    USER_TYPES = [
        ('admin', 'Admin'),
        ('manager', 'Kitchen Manager'),
        ('member', 'Family Member'),
    ]

    LOGIN_ID = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    user_password = models.CharField(max_length=255)
    user_type = models.CharField(max_length=15, choices=USER_TYPES)
    email = models.EmailField(unique=True)
    user_phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_login'

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    def set_password(self, raw_password):
        self.user_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.user_password)


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'accounts_password_reset_otp'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username}"
