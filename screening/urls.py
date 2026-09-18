from django.urls import path
from . import views

urlpatterns = [
    path('api/patients/', views.api_patients, name='api_patients'),
    path('api/screening/<str:patient_id>/', views.api_screening, name='api_screening'),
    path('api/create_screening/', views.api_create_screening, name='api_create_screening'),
    path('api/referral/<int:screening_id>/', views.api_generate_referral, name='api_referral'),
    path('api/auth/register/', views.api_register, name='api_register'),
    path('api/auth/login/', views.api_login, name='api_login'),
    path('api/admin/employees/', views.api_admin_employees, name='api_admin_employees'),
    path('api/admin/employees/<int:employee_id>/', views.api_admin_employees, name='api_admin_employee_detail'),
]