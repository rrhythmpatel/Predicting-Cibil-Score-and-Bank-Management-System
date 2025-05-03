from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    account_number = models.CharField(max_length=20, unique=True, null=True)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=True)  # Add this field
    pin = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.account_number}"

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.is_approved = True
            self.is_pending = False
        super().save(*args, **kwargs)

class ChequeDeposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cheque_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    payee_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_issue = models.DateField(blank=True, null=True)
    deposit_account = models.CharField(max_length=50, blank=True, null=True)
    deposit_date = models.DateTimeField(auto_now_add=True)
    front_image = models.ImageField(upload_to='cheque_images/', blank=True, null=True)
    back_image = models.ImageField(upload_to='cheque_images/', blank=True, null=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cheques')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Cheque {self.cheque_number} - {self.amount}"

class ChequeStatus(models.Model):
    cheque = models.ForeignKey(ChequeDeposit, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    class Meta:
        ordering = ['-timestamp']

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('transfer', 'Transfer'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('cheque', 'Cheque'),
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transactions', null=True, blank=True)  # Made nullable
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add charges field
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='transfer')  # Added default value
    reference_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Made nullable
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='completed')
    is_approved = models.BooleanField(default=False)  # Add is_approved field

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} from {self.sender} to {self.recipient}"

    class Meta:
        ordering = ['-timestamp']

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('transaction', 'Transaction'),
        ('loan', 'Loan'),
        ('account', 'Account'),
        ('system', 'System'),
        ('cheque', 'Cheque'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')

    def __str__(self):
        return f"Notification for {self.user.username}"

    class Meta:
        ordering = ['-created_at']

class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LoanApplication(models.Model):
    LOAN_TYPES = (
        ('personal', 'Personal Loan'),
        ('home', 'Home Loan'),
        ('car', 'Car Loan'),
        ('education', 'Education Loan'),
        ('business', 'Business Loan'),
    )
    
    EMPLOYMENT_STATUS = (
        ('employed', 'Employed'),
        ('self_employed', 'Self Employed'),
        ('business', 'Business Owner'),
        ('student', 'Student'),
        ('retired', 'Retired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loan_applications')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES, default='personal')
    purpose = models.TextField(blank=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added default value
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='employed')  # Added default value
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    applied_date = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add to default
    client_name = models.CharField(max_length=255, blank=True)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=15, blank=True)
    client_address = models.TextField(blank=True)

    def __str__(self):
        return f"LoanApplication {self.id} - {self.status}"

    class Meta:
        ordering = ['-created_at']

class CibilScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}"


# Add this to your existing models.py file

# Add this import at the top of your file
from django.contrib.auth.models import User
# If Account is defined in the same file, you don't need to import it
# If Account is defined in another file, you need to import it

# Add this before the Investment model

class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=[
        ('savings', 'Savings'),
        ('checking', 'Checking'),
        ('investment', 'Investment')
    ], default='savings')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_type} - {self.account_number}"

class Investment(models.Model):
    INVESTMENT_TYPES = [
        ('stock', 'Stocks'),
        ('bond', 'Bonds'),
        ('mutual_fund', 'Mutual Funds'),
        ('etf', 'ETFs'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES, default='stock')
    symbol = models.CharField(max_length=10, default='UNKNOWN')
    stock_name = models.CharField(max_length=100, default='Unknown Stock')
    shares = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate amount if not provided
        if not self.amount:
            self.amount = self.shares * self.purchase_price
        
        # Calculate current value if current price is available
        if self.current_price:
            self.current_value = self.shares * self.current_price
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.stock_name} ({self.symbol}) - {self.shares} shares"
    
    def calculate_returns(self):
        """Calculate the returns on the investment"""
        return self.current_value - self.amount
    
    def calculate_return_percentage(self):
        """Calculate the percentage return on the investment"""
        if self.amount > 0:
            return (self.calculate_returns() / self.amount) * 100
        return 0

# Add this to your models.py file
class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)
    # Add to your User model
    daily_transfer_limit = models.DecimalField(
    max_digits=12, 
    decimal_places=2, 
    default=5000.00,
    help_text="Maximum amount the user can transfer in a single day"
    )
    
    def __str__(self):
        return f"Preferences for {self.user.username}"










