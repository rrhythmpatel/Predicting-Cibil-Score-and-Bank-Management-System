from django.urls import path
from . import views

urlpatterns = [
    path('quick-transfer/', views.quick_transfer, name='quick_transfer'),
    path('quick-transfer/process/', views.process_quick_transfer, name='process_quick_transfer'),
    path('validate-recipient/<str:account_number>/', views.validate_recipient, name='validate_recipient'),
    path('get-recipient-name/', views.get_recipient_name, name='get_recipient_name'),
    path('get-transaction-data/', views.get_transaction_data, name='get_transaction_data'),
    path('cheque-deposit/', views.cheque_deposit, name='cheque_deposit'),
    path('upload-cheque/', views.upload_cheque, name='upload_cheque'),
    path('status-tracking/', views.status_tracking, name='status_tracking'),
    
    # Add these new URL patterns
    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('mark_all_notifications_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('approve_user/', views.approve_user, name='approve_user'),
    path('get_user_loan_eligibility/', views.get_user_loan_eligibility, name='get_user_loan_eligibility'),
    path('process_loan_review/', views.process_loan_decision, name='process_loan_review'),
    path('submit_loan_application/', views.submit_loan_application, name='submit_loan_application'),
    path('loan/', views.loan_normal, name='loan'),
    path('process_loan_application/', views.process_loan_application, name='process_loan_application'),
    path('create_loan_notification/', views.create_loan_notification, name='create_loan_notification'),
    path('api/accounts/', views.get_user_accounts, name='get_user_accounts'),
    path('cheque_deposit/', views.cheque_deposit, name='cheque_deposit'),
    path('upload_cheque/', views.upload_cheque, name='upload_cheque'),
    path('status_tracking/', views.status_tracking, name='status_tracking'),
    path('process_transaction/', views.process_transaction, name='process_transaction'),
    path('credit_account/', views.credit_account, name='credit_account'),
    path('get_account_holder/', views.get_account_holder, name='get_account_holder'),
    
    # Add this new URL pattern for approve_cheque_deposit
    path('approve_cheque_deposit/', views.approve_cheque_deposit, name='approve_cheque_deposit'),
    
    # Add this new URL pattern for create_cheque_deposit
    path('create_cheque_deposit/', views.create_cheque_deposit, name='create_cheque_deposit'),
    
    # Add these URL patterns
    path('reject_cheque_deposit/', views.reject_cheque_deposit, name='reject_cheque_deposit'),
    path('get_cheque_deposit_details/<str:deposit_id>/', views.get_cheque_deposit_details, name='get_cheque_deposit_details'),
    path('debug-cheque-deposits/', views.debug_cheque_deposits, name='debug_cheque_deposits'),
    path('get_pending_cheque_deposits/', views.get_pending_cheque_deposits, name='get_pending_cheque_deposits'),
    
    # Investment URLs
    path('api/market_data/', views.api_market_data, name='api_market_data'),
    path('api/stock_data/<str:symbol>/', views.api_stock_data, name='api_stock_data'),
    path('investment/', views.investment_page, name='investment_page'),
    # Make sure you have a URL pattern like this:
    path('investments/', views.view_investments, name='view_investments'),
    path('investment/sell/<int:investment_id>/', views.sell_investment, name='sell_investment_page'),
    path('investment/process-sell/<int:investment_id>/', views.process_sell_investment, name='process_sell_investment'),
    path('investment/create/', views.create_investment, name='create_investment'),
    path('api/sell_investment/', views.api_sell_investment, name='api_sell_investment'),
    path('api/investments/real-time/', views.api_investment_real_time, name='api_investment_real_time'),
    # Add this to your urlpatterns
    path('api/user-accounts/', views.api_user_accounts, name='api_user_accounts'),
    # Add this to your urlpatterns
    path('api/stock-data/', views.stock_data_api, name='stock_data_api'),
    # Add this to your urlpatterns list
    path('api/market-data/', views.get_market_data, name='market_data'),
     path('api/create-account/', views.create_account_api, name='create_account_api'),
    # Add this to your urlpatterns list
    path('api/investments/', views.api_investments, name='api_investments'),

     path('help/', views.help_view, name='help'),
     
     
]