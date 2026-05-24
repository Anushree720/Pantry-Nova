from django.db import models
from accounts.models import Login
from households.models import Household
from inventory.models import Category


class WasteLog(models.Model):
    REASONS = [
        ('expired', 'Expired'),
        ('overcooked', 'Overcooked'),
        ('spoiled', 'Spoiled'),
        ('over_purchased', 'Over-purchased'),
        ('other', 'Other'),
    ]

    waste_id = models.AutoField(primary_key=True)
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    logged_by = models.ForeignKey(Login, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20, default='kg')
    reason = models.CharField(max_length=30, choices=REASONS, default='expired')
    estimated_cost = models.FloatField(default=0)
    co2_equivalent = models.FloatField(default=0)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waste_waste_log'
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.item_name} - {self.quantity}{self.unit}"
