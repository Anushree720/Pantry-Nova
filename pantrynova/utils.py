"""Shared utility functions for Pantry Nova."""
import random
import string


CO2_FACTORS = {
    'meat': 27.0,
    'dairy': 3.2,
    'produce': 2.0,
    'vegetables': 2.0,
    'fruits': 2.0,
    'grains': 1.4,
    'other': 1.8,
}


def calculate_co2(category_name, quantity_kg):
    """Calculate CO2 equivalent (kg) for wasted food."""
    if not quantity_kg or quantity_kg <= 0:
        return 0.0
    if not category_name:
        factor = CO2_FACTORS['other']
    else:
        key = category_name.lower().strip()
        factor = CO2_FACTORS.get(key, CO2_FACTORS['other'])
        # Try partial match
        if key not in CO2_FACTORS:
            for k, v in CO2_FACTORS.items():
                if k in key or key in k:
                    factor = v
                    break
    return round(float(quantity_kg) * factor, 2)


def to_kg(quantity, unit):
    """Convert quantity to kg for CO2 calc."""
    if quantity is None:
        return 0
    unit = (unit or '').lower()
    if unit == 'kg':
        return float(quantity)
    if unit == 'g':
        return float(quantity) / 1000.0
    if unit == 'l':
        return float(quantity)  # Approx 1L ~ 1kg for water-based
    if unit == 'ml':
        return float(quantity) / 1000.0
    # pcs, packets, other -> rough estimate 0.25 kg per unit
    return float(quantity) * 0.25


def generate_join_code(length=6):
    """Generate uppercase alphanumeric join code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_otp(length=6):
    """Generate numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))
