"""Seed Pantry Nova with admin user, sample household, manager, members and items."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

from accounts.models import Login
from households.models import Household
from managers.models import KitchenManager
from members.models import FamilyMember
from inventory.models import Category, PantryItem
from waste.models import WasteLog
from subscriptions.models import Plan, Subscription


class Command(BaseCommand):
    help = 'Seed Pantry Nova with sample data (admin, household, manager, members, items).'

    def handle(self, *args, **opts):
        self.stdout.write(self.style.NOTICE('🌿 Loading fixtures...'))
        try:
            call_command('loaddata', 'categories', verbosity=0)
            call_command('loaddata', 'ingredients', verbosity=0)
            self.stdout.write(self.style.SUCCESS('  ✓ Fixtures loaded.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! Fixture loading failed: {e}'))

        with transaction.atomic():
            # ===== Subscription Plans =====
            plan_data = [
                {
                    'name': 'Free', 'slug': 'free',
                    'tagline': 'Get started with the basics — perfect for small families.',
                    'price_monthly': 0, 'price_yearly': 0,
                    'max_items': 50, 'max_members': 1,
                    'ai_access': False, 'advanced_analytics': False,
                    'pdf_csv_export': False, 'priority_support': False,
                    'badge_color': 'primary', 'sort_order': 1,
                },
                {
                    'name': 'Pro', 'slug': 'pro',
                    'tagline': 'For active households who want full Nova AI and analytics.',
                    'price_monthly': 299, 'price_yearly': 2999,
                    'max_items': 500, 'max_members': 5,
                    'ai_access': True, 'advanced_analytics': True,
                    'pdf_csv_export': True, 'priority_support': False,
                    'badge_color': 'accent', 'sort_order': 2,
                },
                {
                    'name': 'Premium', 'slug': 'premium',
                    'tagline': 'Unlimited everything — for restaurants, hotels & large families.',
                    'price_monthly': 499, 'price_yearly': 4999,
                    'max_items': -1, 'max_members': -1,
                    'ai_access': True, 'advanced_analytics': True,
                    'pdf_csv_export': True, 'priority_support': True,
                    'badge_color': 'warning', 'sort_order': 3,
                },
            ]
            for pd in plan_data:
                Plan.objects.update_or_create(slug=pd['slug'], defaults=pd)
            self.stdout.write(self.style.SUCCESS('  ✓ Subscription plans seeded (Free, Pro, Premium).'))

            # ===== Admin =====
            if not Login.objects.filter(username='admin').exists():
                admin = Login(
                    username='admin',
                    email='admin@pantrynova.com',
                    user_type='admin',
                    user_phone='+919999999999',
                )
                admin.set_password('admin123')
                admin.save()
                self.stdout.write(self.style.SUCCESS('  ✓ Admin user created. (admin / admin123)'))
            else:
                self.stdout.write('  · Admin user already exists.')

            # ===== Sample Household =====
            household, hcreated = Household.objects.get_or_create(
                join_code='DEMO01',
                defaults={
                    'household_name': 'The Sharma Family',
                    'household_type': 'home',
                    'address': '123 Greenfield Road',
                    'city': 'Bengaluru',
                    'pin_code': '560001',
                    'is_verified': True,
                },
            )
            if hcreated:
                self.stdout.write(self.style.SUCCESS('  ✓ Sample household created.'))

            # ===== Manager =====
            if not Login.objects.filter(username='manager').exists():
                m_login = Login(
                    username='manager',
                    email='manager@pantrynova.com',
                    user_type='manager',
                    user_phone='+919876543210',
                )
                m_login.set_password('manager123')
                m_login.save()
                KitchenManager.objects.create(
                    login=m_login,
                    household=household,
                    full_name='Anjali Sharma',
                    phone='+919876543210',
                )
                self.stdout.write(self.style.SUCCESS('  ✓ Manager user created. (manager / manager123)'))
            else:
                self.stdout.write('  · Manager user already exists.')

            # ===== Subscription for sample household =====
            free_plan = Plan.objects.get(slug='free')
            Subscription.objects.get_or_create(
                household=household,
                defaults={'plan': free_plan, 'status': 'active'},
            )

            # ===== Family Member =====
            if not Login.objects.filter(username='member').exists():
                m_login = Login(
                    username='member',
                    email='member@pantrynova.com',
                    user_type='member',
                    user_phone='+919876543211',
                )
                m_login.set_password('member123')
                m_login.save()
                FamilyMember.objects.create(
                    login=m_login,
                    household=household,
                    full_name='Rahul Sharma',
                    phone='+919876543211',
                )
                self.stdout.write(self.style.SUCCESS('  ✓ Member user created. (member / member123)'))
            else:
                self.stdout.write('  · Member user already exists.')

            # ===== Sample Pantry Items =====
            if not PantryItem.objects.filter(household=household).exists():
                today = date.today()
                samples = [
                    ('Tomatoes', 1, 0.5, 'kg', 'fridge', -1),       # expired
                    ('Spinach', 1, 1.0, 'packets', 'fridge', 2),    # expiring soon
                    ('Milk', 3, 1.0, 'L', 'fridge', 3),             # expiring soon
                    ('Chicken', 4, 1.5, 'kg', 'fridge', 1),         # critical
                    ('Apples', 2, 1.0, 'kg', 'fridge', 10),         # fresh
                    ('Rice', 5, 5.0, 'kg', 'pantry', 200),          # fresh
                    ('Lentils (Dal)', 5, 2.0, 'kg', 'pantry', 250), # fresh
                    ('Turmeric', 6, 0.2, 'kg', 'pantry', 400),      # fresh
                    ('Onions', 1, 2.0, 'kg', 'pantry', 20),         # fresh
                    ('Bread', 5, 1.0, 'packets', 'counter', 0),     # expiring today
                    ('Yogurt', 3, 0.5, 'kg', 'fridge', 5),          # expiring this week
                    ('Bananas', 2, 1.2, 'kg', 'counter', 4),        # expiring soon
                ]
                m = KitchenManager.objects.get(household=household)
                for name, cat_id, qty, unit, storage, days_offset in samples:
                    try:
                        cat = Category.objects.get(pk=cat_id)
                    except Category.DoesNotExist:
                        cat = None
                    PantryItem.objects.create(
                        household=household,
                        added_by=m.login,
                        item_name=name,
                        category=cat,
                        quantity=qty,
                        unit=unit,
                        purchase_date=today - timedelta(days=2),
                        expiry_date=today + timedelta(days=days_offset),
                        storage_location=storage,
                    )
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(samples)} sample pantry items created.'))

                # Sample waste logs
                WasteLog.objects.create(
                    household=household, logged_by=m.login,
                    item_name='Cucumbers', category=Category.objects.get(pk=1),
                    quantity=0.3, unit='kg', reason='spoiled', estimated_cost=40,
                )
                WasteLog.objects.create(
                    household=household, logged_by=m.login,
                    item_name='Bread', category=Category.objects.get(pk=5),
                    quantity=0.5, unit='kg', reason='expired', estimated_cost=30,
                )
                self.stdout.write(self.style.SUCCESS('  ✓ Sample waste logs created.'))

        self.stdout.write(self.style.SUCCESS('\n🌿 Pantry Nova seeded successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:   admin / admin123      → /login/admin/')
        self.stdout.write('  Manager: manager / manager123  → /login/manager/')
        self.stdout.write('  Member:  member / member123    → /login/member/')
        self.stdout.write('  Member join code: DEMO01\n')
