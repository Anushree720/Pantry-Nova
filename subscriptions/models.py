from datetime import timedelta
from django.db import models
from django.utils import timezone

from households.models import Household


class Plan(models.Model):
    """Subscription plan — Free, Pro, Premium."""
    SLUG_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]

    plan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=20, unique=True, choices=SLUG_CHOICES)
    tagline = models.CharField(max_length=200, blank=True)
    price_monthly = models.IntegerField(default=0, help_text='Price in INR per month')
    price_yearly = models.IntegerField(default=0, help_text='Price in INR per year')
    max_items = models.IntegerField(default=50, help_text='-1 = unlimited')
    max_members = models.IntegerField(default=1, help_text='-1 = unlimited')
    ai_access = models.BooleanField(default=False)
    advanced_analytics = models.BooleanField(default=False)
    pdf_csv_export = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    badge_color = models.CharField(max_length=20, default='accent')
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'subscriptions_plan'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name} (Rs.{self.price_monthly}/mo)"

    @property
    def is_free(self):
        return self.price_monthly == 0

    @property
    def yearly_savings(self):
        if self.price_monthly == 0:
            return 0
        return (self.price_monthly * 12) - self.price_yearly

    @property
    def yearly_savings_pct(self):
        if self.price_monthly == 0:
            return 0
        return round((self.yearly_savings / (self.price_monthly * 12)) * 100)

    def feature_list(self):
        items_label = 'Unlimited items' if self.max_items < 0 else f'Up to {self.max_items} items'
        members_label = 'Unlimited members' if self.max_members < 0 else f'{self.max_members} family member{"s" if self.max_members != 1 else ""}'
        feats = [items_label, members_label, 'Smart expiry alerts']
        if self.ai_access:
            feats.append('Nova AI assistant')
        else:
            feats.append('Basic AI (limited)')
        if self.advanced_analytics:
            feats.append('Advanced analytics & charts')
        else:
            feats.append('Basic analytics')
        if self.pdf_csv_export:
            feats.append('PDF & CSV exports')
        if self.priority_support:
            feats.append('Priority email support')
        feats.append('Shopping list automation')
        feats.append('Waste tracking & CO2 insights')
        return feats


class Subscription(models.Model):
    """Active subscription tied to a Household."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    sub_id = models.AutoField(primary_key=True)
    household = models.OneToOneField(Household, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES, default='monthly')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'subscriptions_subscription'

    def __str__(self):
        return f"{self.household.household_name} - {self.plan.name}"

    @property
    def is_active_now(self):
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def days_left(self):
        if not self.expires_at:
            return None
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def renew(self, billing_cycle=None):
        cycle = billing_cycle or self.billing_cycle
        days = 30 if cycle == 'monthly' else 365
        base = self.expires_at if (self.expires_at and self.expires_at > timezone.now()) else timezone.now()
        self.expires_at = base + timedelta(days=days)
        self.status = 'active'
        self.billing_cycle = cycle
        self.cancelled_at = None
        self.save()


class Payment(models.Model):
    """Demo payment record. No real money handled."""
    METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.AutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    amount = models.IntegerField(help_text='Amount in INR')
    currency = models.CharField(max_length=3, default='INR')
    billing_cycle = models.CharField(max_length=10, default='monthly')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='card')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    transaction_id = models.CharField(max_length=64, unique=True)
    masked_account = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions_payment'
        ordering = ['-created_at']

    def __str__(self):
        return f"Rs.{self.amount} - {self.plan.name} - {self.transaction_id}"
