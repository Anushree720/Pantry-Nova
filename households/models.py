from django.db import models


class Household(models.Model):
    HOUSEHOLD_TYPES = [
        ('home', 'Home'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
        ('canteen', 'Canteen'),
        ('school', 'School'),
    ]

    household_id = models.AutoField(primary_key=True)
    household_name = models.CharField(max_length=100)
    household_type = models.CharField(max_length=20, choices=HOUSEHOLD_TYPES, default='home')
    address = models.TextField()
    city = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=10)
    join_code = models.CharField(max_length=6, unique=True)
    is_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'households_household'
        ordering = ['-created_at']

    def __str__(self):
        return self.household_name

    @property
    def member_count(self):
        return self.familymember_set.count()

    @property
    def item_count(self):
        return self.pantryitem_set.filter(is_consumed=False).count()
