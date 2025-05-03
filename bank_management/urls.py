from django.urls import path
from .core import views  # Make sure this import is correct

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('fund-transfer/', views.fund_transfer, name='fund_transfer'),
    path('logout/', views.user_logout, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
    # CIBIL data endpoint
    path('get_cibil_data/<int:client_id>/', views.get_cibil_data, name='get_cibil_data'),
    # Add these missing endpoints for loan functionality
    path('get_loan_applications/', views.get_loan_applications, name='get_loan_applications'),
    path('get_loan_details/<int:loan_id>/', views.get_loan_details, name='get_loan_details'),
    path('process_loan_decision/', views.process_loan_decision, name='process_loan_decision'),
    path('get_admin_stats/', views.get_admin_stats, name='get_admin_stats'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('approve_user/', views.approve_user, name='approve_user'),
    path('api/cibil_score/<int:user_id>/', views.get_cibil_data, name='api_cibil_score'),
    # Add spending overview path with the correct name
    path('spending-overview/', views.spending_overview, name='spending_overview'),
    # Add transaction data endpoint
    path('get_transaction_data/', views.get_transaction_data, name='get_transaction_data'),
    # Add dashboard path
    path('dashboard/', views.dashboard, name='dashboard'),
    # Add this URL pattern to your urlpatterns list
    # Make sure this path is using the correct view function
    path('process_transaction/', views.process_transaction, name='process_transaction'),

    path('get_cheque_deposit_details/<str:deposit_id>/', views.get_cheque_deposit_details, name='get_cheque_deposit_details'),
    # Add this new URL pattern
    path('investment/new/', views.create_investment_page, name='create_investment_page'),
    path('investments/', views.view_investments, name='view_investments'),
    # API endpoints for investment data
    path('api/market_data/', views.api_market_data, name='api_market_data'),
    path('api/stock_data/<str:symbol>/', views.api_stock_data, name='api_stock_data'),
    path('api/account_balance/<int:account_id>/', views.get_account_balance, name='get_account_balance'),
    # Make sure this URL pattern exists
    path('api/sell_investment/', views.sell_investment, name='sell_investment'),
    # Add the process_sell_investment URL pattern
    path('investment/sell/<int:investment_id>/', views.sell_investment, name='sell_investment_page'),
    path('investment/process_sell/<int:investment_id>/', views.process_sell_investment, name='process_sell_investment'),
]