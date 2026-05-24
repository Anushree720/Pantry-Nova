from django import forms
from django.core.exceptions import ValidationError
from .models import Login


class ManagerRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    username = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(min_length=6, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(max_length=15)
    household_name = forms.CharField(max_length=100)
    household_type = forms.ChoiceField(choices=[
        ('home', 'Home'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
        ('canteen', 'Canteen'),
        ('school', 'School'),
    ])
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=50)
    pin_code = forms.CharField(max_length=10)

    def clean_username(self):
        u = self.cleaned_data['username'].strip()
        if Login.objects.filter(username=u).exists():
            raise ValidationError('Username already exists.')
        return u

    def clean_email(self):
        e = self.cleaned_data['email'].strip().lower()
        if Login.objects.filter(email=e).exists():
            raise ValidationError('Email already registered.')
        return e

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise ValidationError('Passwords do not match.')
        return cleaned


class MemberRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    username = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(min_length=6, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(max_length=15)
    join_code = forms.CharField(max_length=6)

    def clean_username(self):
        u = self.cleaned_data['username'].strip()
        if Login.objects.filter(username=u).exists():
            raise ValidationError('Username already exists.')
        return u

    def clean_email(self):
        e = self.cleaned_data['email'].strip().lower()
        if Login.objects.filter(email=e).exists():
            raise ValidationError('Email already registered.')
        return e

    def clean_join_code(self):
        from households.models import Household
        code = self.cleaned_data['join_code'].strip().upper()
        if not Household.objects.filter(join_code=code).exists():
            raise ValidationError('Invalid household join code.')
        return code

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise ValidationError('Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
