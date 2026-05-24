from django.db import models
from households.models import Household
from inventory.models import Category


class ShoppingList(models.Model):
    list_id = models.AutoField(primary_key=True)
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='Shopping List')
    is_auto_generated = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shopping_shopping_list'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.household.household_name})"

    @property
    def items_count(self):
        return self.shoppingitem_set.count()

    @property
    def purchased_count(self):
        return self.shoppingitem_set.filter(is_purchased=True).count()


class ShoppingItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.FloatField(default=1)
    unit = models.CharField(max_length=20, default='pcs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_purchased = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'shopping_shopping_item'

    def __str__(self):
        return self.item_name
