from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='manager_dashboard'),

    path('inventory/', views.inventory_list, name='manager_inventory'),
    path('inventory/save/', views.inventory_save, name='manager_inventory_save'),
    path('inventory/delete/<int:item_id>/', views.inventory_delete, name='manager_inventory_delete'),
    path('inventory/consume/<int:item_id>/', views.inventory_consume, name='manager_inventory_consume'),

    path('expiry-alerts/', views.expiry_alerts, name='manager_expiry'),
    path('expiry-alerts/log-waste/<int:item_id>/', views.expiry_log_waste, name='manager_expiry_log_waste'),

    path('shopping-list/', views.shopping_list, name='manager_shopping'),
    path('shopping-list/add/', views.shopping_add, name='manager_shopping_add'),
    path('shopping-list/toggle/<int:item_id>/', views.shopping_toggle, name='manager_shopping_toggle'),
    path('shopping-list/delete/<int:item_id>/', views.shopping_delete, name='manager_shopping_delete'),
    path('shopping-list/complete/<int:list_id>/', views.shopping_complete, name='manager_shopping_complete'),

    path('waste-log/', views.waste_log, name='manager_waste'),
    path('waste-log/save/', views.waste_save, name='manager_waste_save'),
    path('waste-log/delete/<int:waste_id>/', views.waste_delete, name='manager_waste_delete'),

    path('analytics/', views.analytics, name='manager_analytics'),

    path('family/', views.family_members, name='manager_family'),
    path('family/remove/<int:member_id>/', views.family_remove, name='manager_family_remove'),

    path('profile/', views.profile, name='manager_profile'),
]
