from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/employees/add/', views.employee_create, name='employee_create'),
    path('admin-dashboard/employees/<int:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('admin-dashboard/employees/<int:employee_id>/toggle-status/', views.employee_toggle_status, name='employee_toggle_status'),
    path('api/patients/', views.api_patients, name='api_patients'),
    path('api/screening/<str:patient_id>/', views.api_screening, name='api_screening'),
    path('api/create_screening/', views.api_create_screening, name='api_create_screening'),
    path('api/referral/<int:screening_id>/', views.api_generate_referral, name='api_referral'),
]