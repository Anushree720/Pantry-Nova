from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import WasteLog
from pantrynova.utils import calculate_co2, to_kg


@receiver(pre_save, sender=WasteLog)
def auto_calculate_co2(sender, instance, **kwargs):
    """Auto-calculate CO2 equivalent before saving WasteLog."""
    cat_name = instance.category.name if instance.category else 'other'
    qty_kg = to_kg(instance.quantity, instance.unit)
    instance.co2_equivalent = calculate_co2(cat_name, qty_kg)
