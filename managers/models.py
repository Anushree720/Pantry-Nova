from django.db import models
from accounts.models import Login
from households.models import Household


class KitchenManager(models.Model):
    manager_id = models.AutoField(primary_key=True)
    login = models.OneToOneField(Login, on_delete=models.CASCADE)
    household = models.OneToOneField(Household, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    class Meta:
        db_table = 'managers_kitchen_manager'

    def __str__(self):
        return f"{self.full_name} ({self.household.household_name})"
