from django.db import models
from accounts.models import Login
from households.models import Household


class FamilyMember(models.Model):
    member_id = models.AutoField(primary_key=True)
    login = models.OneToOneField(Login, on_delete=models.CASCADE)
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_family_member'
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.full_name} ({self.household.household_name})"
