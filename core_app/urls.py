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
    path('search/', views.global_search, name='global_search'),
    path('export/devices/csv/', views.export_devices_csv, name='export_devices_csv'),
    path('export/tickets/pdf/', views.export_tickets_pdf, name='export_tickets_pdf'),
    path('admin-panel/devices/bulk/', views.admin_bulk_devices, name='admin_bulk_devices'),

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
    path('admin-panel/maintenance-tracking/', views.admin_tickets, name='admin_tickets'),

    # Maintenance (Tech)
    path('maintenance/', views.tech_dashboard, name='tech_dashboard'),
    path('maintenance/tickets/', views.tech_tickets, name='tech_tickets'),
    path('maintenance/assign/<int:pk>/', views.tech_assign_ticket, name='tech_assign_ticket'),
    path('maintenance/handle/<int:pk>/', views.tech_handle_ticket, name='tech_handle_ticket'),
    path('maintenance/report/edit/<int:pk>/', views.tech_edit_report, name='tech_edit_report'),
    path('maintenance/report/delete/<int:pk>/', views.tech_delete_report, name='tech_delete_report'),

    # Gestion Tickets (User)
    path('my-space/ticket/edit/<int:pk>/', views.user_edit_ticket, name='user_edit_ticket'),
    path('my-space/ticket/delete/<int:pk>/', views.user_delete_ticket, name='user_delete_ticket'),
    path('ticket/<int:pk>/chat/', views.ticket_chat, name='ticket_chat'),

    # User
    path('my-space/', views.user_dashboard, name='user_dashboard'),
    path('my-space/report-issue/', views.user_report_issue, name='user_report_issue'),

    # AI Agent
    path('api/ai-agent/', views.ai_voice_agent, name='ai_voice_agent'),
]
