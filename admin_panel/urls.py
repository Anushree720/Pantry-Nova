from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='admin_dashboard'),

    path('ingredients/', views.ingredients, name='admin_ingredients'),
    path('ingredients/save/', views.ingredient_save, name='admin_ingredient_save'),
    path('ingredients/delete/<int:ref_id>/', views.ingredient_delete, name='admin_ingredient_delete'),

    path('households/', views.households_list, name='admin_households'),
    path('households/<int:household_id>/', views.household_view, name='admin_household_view'),
    path('households/<int:household_id>/verify/', views.household_verify, name='admin_household_verify'),
    path('households/<int:household_id>/suspend/', views.household_suspend, name='admin_household_suspend'),

    path('telemetry/', views.telemetry, name='admin_telemetry'),

    path('complaints/', views.complaints_list, name='admin_complaints'),
    path('complaints/<int:complaint_id>/reply/', views.complaint_reply, name='admin_complaint_reply'),

    path('feedback/', views.feedback_list, name='admin_feedback'),
]
