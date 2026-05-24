from django.db import models
from inventory.models import Category


class IngredientReference(models.Model):
    STORAGE_TYPES = [
        ('fridge', 'Fridge'),
        ('freezer', 'Freezer'),
        ('pantry', 'Pantry'),
        ('counter', 'Counter'),
    ]

    ref_id = models.AutoField(primary_key=True)
    ingredient_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    default_shelf_life_days = models.IntegerField(default=7)
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPES, default='pantry')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_panel_ingredient_reference'
        ordering = ['ingredient_name']

    def __str__(self):
        return self.ingredient_name
