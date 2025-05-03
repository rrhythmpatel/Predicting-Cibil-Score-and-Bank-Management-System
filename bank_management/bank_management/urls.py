"""
URL configuration for bank_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from core import views
from django.contrib.auth import views as auth_views
from core.views import transaction_data  # Ensure correct import
from core.views import get_cibil_data
from core.views import spending_overview
# Import the get_transaction_data view - fix the import path
from core.views import get_transaction_data  # Changed from bank_management.views to .views
from core.views import export_loan_data
from django.urls import path
from core import views
from views import (
    admin_panel, dashboard, login_view, user_logout, fund_transfer,
    get_cibil_data, get_loan_details, get_account_balance,
    download_transaction_report  # Add this import
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('fund-transfer/', views.fund_transfer, name='fund_transfer'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('loan/', views.loan_normal, name='loan_normal'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
    path('get_admin_stats/', views.get_admin_stats, name='get_admin_stats'),

    # Loan related URLs
    path('submit_loan_application/', views.submit_loan_application, name='submit_loan_application'),
    path('get_loan_applications/', views.get_loan_applications, name='get_loan_applications'),
    path('get_loan_details/<int:loan_id>/', views.get_loan_details, name='get_loan_details'),
    path('process_loan_decision/', views.process_loan_decision, name='process_loan_decision'),

    # Transaction & Activity URLs
    path('get_recent_activities/', views.get_recent_activities, name='get_recent_activities'),
    path('get_transaction_volume/', views.get_transaction_volume, name='get_transaction_volume'),
    path('api/transactions/', transaction_data, name='transaction_data'),
    # Add the get_transaction_data URL
    path('get_transaction_data/', get_transaction_data, name='get_transaction_data'),
    path('get_user_balance/', views.get_user_balance, name='get_user_balance'),

    # Report Download
    path('download_transaction_report/', download_transaction_report, name='download_transaction_report'),

    # Include core app URLs
    path('', include('core.urls')),

    # Make sure this URL pattern exists in your urls.py file
    # Add this to your urlpatterns list
    path('cibil-score/', views.cibil_score, name='cibil_score'),
    # Add this to your urlpatterns
    path('cibil-score/refresh/', views.refresh_cibil_score, name='refresh_cibil_score'),
    
    # Add this URL to fetch CIBIL data for loan interest rates
    path('cibil-score/<int:user_id>/', get_cibil_data, name='get_cibil_data'),
    path('spending-overview/', spending_overview, name='spending_overview'),

    path('validate-recipient/<str:account_number>/', views.validate_recipient, name='validate_recipient'),
    path('quick-transfer/', views.quick_transfer, name='quick_transfer'),
    # Add this to your urlpatterns list
    path('credit_account/', views.credit_account, name='credit_account'),
    # Add this to your urlpatterns list
    # Add these URL patterns if they don't exist
    path('investment/', views.investment_page, name='investment_page'),
    path('investment/create/', views.create_investment, name='create_investment'),
    # Add this to your urlpatterns list
    # Add this to your urlpatterns list
    path('immediate-approve-cheque/', views.immediate_approve_cheque, name='immediate_approve_cheque'),
    # Fix this line - change core_views to views
    path('api/user_accounts/', views.api_user_accounts, name='api_user_accounts'),
    path('settings/', views.settings, name='settings'),
    path('account/management/', views.account_management, name='account_management'),

     path('export_loan_data/', views.export_loan_data, name='export_loan_data'),
    
 # Add this to your urlpatterns list
path('get_client_details/', views.get_client_details, name='get_client_details'),   
# Add these URL patterns to your urls.py file

    path('change-password/', views.change_password, name='change_password'),
    path('change-pin/', views.change_pin, name='change_pin'),
    path('update-personal-info/', views.update_personal_info, name='update_personal_info'),

path('update_notification_preferences/', views.update_notification_preferences, name='update_notification_preferences'),
# Add this to your urlpatterns list
path('download-statement/', views.download_statement, name='download_statement'),
    path('services/', views.services, name='services'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact/', views.contact, name='contact'),
    # Add these URL patterns to your urlpatterns list
    
    path('get-started/', views.get_started, name='get_started'),
    path('learn-more/', views.learn_more, name='learn_more'),
    path('download-app/', views.download_app, name='download_app'),
    path('security-features/', views.security_features, name='security_features'),
    path('update-limits/', views.update_limits, name='update_limits'),
]
