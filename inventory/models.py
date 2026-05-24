from datetime import date
from django.db import models

from accounts.models import Login
from households.models import Household


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, default='bi-egg-fried')
    color_code = models.CharField(max_length=7, default='#52B788')

    class Meta:
        db_table = 'inventory_category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class PantryItem(models.Model):
    UNITS = [
        ('kg', 'kg'), ('g', 'g'), ('L', 'L'), ('ml', 'ml'),
        ('pcs', 'pcs'), ('packets', 'packets'), ('other', 'other'),
    ]
    STORAGES = [
        ('fridge', 'Fridge'),
        ('freezer', 'Freezer'),
        ('pantry', 'Pantry'),
        ('counter', 'Counter'),
    ]

    item_id = models.AutoField(primary_key=True)
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    added_by = models.ForeignKey(Login, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.FloatField(default=1)
    unit = models.CharField(max_length=20, choices=UNITS, default='pcs')
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    storage_location = models.CharField(max_length=20, choices=STORAGES, default='pantry')
    barcode = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    threshold = models.FloatField(default=0.5)
    is_consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_pantry_item'
        ordering = ['expiry_date']

    def __str__(self):
        return self.item_name

    @property
    def days_until_expiry(self):
        return (self.expiry_date - date.today()).days

    @property
    def expiry_status(self):
        days = self.days_until_expiry
        if days < 0:
            return 'expired'
        elif days <= 1:
            return 'critical'
        elif days <= 7:
            return 'expiring_soon'
        else:
            return 'fresh'

    @property
    def expiry_color(self):
        s = self.expiry_status
        if s in ('expired', 'critical'):
            return 'danger'
        if s == 'expiring_soon':
            return 'warning'
        return 'success'

    @property
    def expiry_label(self):
        s = self.expiry_status
        if s == 'expired':
            return 'Expired'
        if s == 'critical':
            return 'Critical'
        if s == 'expiring_soon':
            return 'Expiring Soon'
        return 'Fresh'
