from django.urls import path
from . import views

urlpatterns = [
    # General
    path('', views.home, name='home'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='account_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin-panel/devices/', views.admin_manage_devices, name='admin_manage_devices'),
    path('admin-panel/devices/add/', views.admin_device_form, name='admin_add_device'),
    path('admin-panel/devices/<int:pk>/success/', views.admin_device_success, name='admin_device_success'),
    path('admin-panel/devices/<int:pk>/edit/', views.admin_device_form, name='admin_edit_device'),
    path('admin-panel/devices/<int:pk>/assign/', views.admin_assign_device, name='admin_assign_device'),
    path('admin-panel/devices/<int:pk>/history/', views.admin_device_history, name='admin_device_history'),
    path('admin-panel/devices/<int:pk>/delete/', views.admin_delete_device, name='admin_delete_device'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/categories/<int:pk>/edit/', views.admin_edit_category, name='admin_edit_category'),
    path('admin-panel/categories/<int:pk>/delete/', views.admin_delete_category, name='admin_delete_category'),
    path('admin-panel/assignments/', views.admin_assign_list, name='admin_assign_list'),

    # Tech
    path('tech-panel/', views.tech_dashboard, name='tech_dashboard'),
    path('tech-panel/tickets/', views.tech_tickets, name='tech_tickets'),
    path('tech-panel/tickets/<int:pk>/handle/', views.tech_handle_ticket, name='tech_handle_ticket'),

    # User
    path('my-space/', views.user_dashboard, name='user_dashboard'),
    path('my-space/report-issue/', views.user_report_issue, name='user_report_issue'),
]
