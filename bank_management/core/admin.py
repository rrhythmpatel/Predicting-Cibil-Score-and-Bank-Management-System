from django.contrib import admin
from .models import (
    User, 
    ChequeDeposit, 
    ChequeStatus, 
    Transaction, 
    Notification, 
    Client, 
    LoanApplication, 
    CibilScore,
    Account,
    Investment,
    UserPreference
)

# Register User model
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'account_number', 'account_balance', 'is_approved', 'is_pending')
    search_fields = ('username', 'account_number', 'email')
    list_filter = ('is_approved', 'is_pending')

# Register ChequeDeposit model
@admin.register(ChequeDeposit)
class ChequeDepositAdmin(admin.ModelAdmin):
    list_display = ('cheque_number', 'user', 'amount', 'bank_name', 'status', 'deposit_date')
    search_fields = ('cheque_number', 'user__username', 'bank_name')
    list_filter = ('status', 'deposit_date')

# Register ChequeStatus model
@admin.register(ChequeStatus)
class ChequeStatusAdmin(admin.ModelAdmin):
    list_display = ('cheque', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')

# Register Transaction model
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'sender', 'recipient', 'amount', 'timestamp', 'status')
    search_fields = ('sender__username', 'recipient__username', 'reference_number')
    list_filter = ('transaction_type', 'status', 'timestamp')

# Register Notification model
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('notification_type', 'is_read', 'created_at')

# Register Client model
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')

# Register LoanApplication model
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'loan_type', 'amount', 'status', 'applied_date')
    search_fields = ('user__username', 'client_name', 'client_email')
    list_filter = ('loan_type', 'status', 'applied_date')

# Register CibilScore model
@admin.register(CibilScore)
class CibilScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'updated_at')
    search_fields = ('user__username',)
    list_filter = ('updated_at',)

# Register Account model
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'account_type', 'balance', 'created_at')
    search_fields = ('user__username', 'account_number')
    list_filter = ('account_type', 'created_at')

# Register Investment model
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment_type', 'symbol', 'stock_name', 'shares', 'purchase_date')
    search_fields = ('user__username', 'symbol', 'stock_name')
    list_filter = ('investment_type', 'purchase_date')

# Register UserPreference model
@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications', 'marketing_emails')
    search_fields = ('user__username',)
    list_filter = ('email_notifications', 'sms_notifications', 'marketing_emails')
