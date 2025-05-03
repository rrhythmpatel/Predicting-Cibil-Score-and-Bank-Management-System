from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Transaction
import uuid
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, F, Func, CharField, Value
from .models import Client  # Explicit import
from .models import LoanApplication, Notification
import csv
from django.http import HttpResponse
import random
from django.db.models import Sum
from django.utils import timezone
import json  # Add this import
from django.utils import timezone
from django.db import models
from core.models import CibilScore
from .models import User, Transaction, Notification, ChequeDeposit
from django.utils.crypto import get_random_string
import time
from django.db import transaction  # ✅ Import transaction for atomic operations
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import datetime
from bs4 import BeautifulSoup
import requests
from .models import Investment, Account, Notification, ChequeDeposit, Transaction
from .utils import schedule_auto_approval
from .models import Investment
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserPreference
import yfinance as tf
from django.db.models import Sum
from django.utils.crypto import get_random_string
from decimal import Decimal
import json
from django.db import transaction

from collections import defaultdict
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test







def homepage(request):
    
    return render(request, 'homepage.html')

def login_view(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate using email as username
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Clear any existing session data before login
            request.session.flush()
            # Perform login
            login(request, user)
            # Store user account details in session
            request.session['user_account'] = {
                'account_number': user.account_number,
                'account_balance': str(user.account_balance),
                'full_name': f"{user.first_name} {user.last_name}",
                'email': user.email
            }
            # Set session expiry
            request.session.set_expiry(3600)  # 1 hour
            return JsonResponse({'success': True, 'message': 'Login successful!', 'redirect_url': '/dashboard/'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid username or password'})
    
    return render(request, 'loginpage.html')

def register(request):
   
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        pin = request.POST.get('pin')
        confirm_pin = request.POST.get('confirm_pin')

        # Validate form data
        if not all([first_name, last_name, email, address, password, confirm_password, pin, confirm_pin]):
            return JsonResponse({'success': False, 'message': 'All fields are required'})

        if password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match'})

        if pin != confirm_pin:
            return JsonResponse({'success': False, 'message': 'PINs do not match'})

        # Create user
        User = get_user_model()
        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Account already registered. Please try with a different email.'})

            # Generate a unique account number
            account_number = str(uuid.uuid4().int)[:10]
            
            # Create user instance with is_active=False for admin approval
            # Only include fields that definitely exist in the model
            user_data = {
                'username': email,
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'address': address,
                'pin': pin,
                'account_number': account_number,
                'is_active': False,
                'is_approved': False,
                'account_balance': Decimal('1000.00')
            }
            
            # Create the user with create_user method
            user = User.objects.create_user(**user_data)
            
            return JsonResponse({'success': True, 'message': 'Account created successfully! Please wait for admin approval before logging in.'})
            
        except Exception as e:
            print(f"Registration error: {str(e)}")  # Add this for debugging
            return JsonResponse({'success': False, 'message': f'Error creating account: {str(e)}'})
            
    return render(request, 'Registration.html')

def registration(request):
   
    return render(request, 'Registration.html')

def fund_transfer(request):
  
    if request.method == 'POST':
        try:
            # Get form data
            recipient_account = request.POST.get('recipient_account')
            amount = Decimal(request.POST.get('amount'))
            pin = request.POST.get('pin')
            note = request.POST.get('note', '')

            # Validate sender's PIN
            if request.user.pin != pin:
                return JsonResponse({'success': False, 'message': 'Invalid PIN number'})

            # Find recipient user
            User = get_user_model()
            try:
                recipient = User.objects.get(account_number=recipient_account)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Recipient account not found'})

            # Check if sender has sufficient balance
            if request.user.account_balance < amount:
                return JsonResponse({'success': False, 'message': 'Insufficient balance'})

            # Generate reference number
            reference_number = str(uuid.uuid4())

            # Create transaction record
            transaction = Transaction.objects.create(
                sender=request.user,
                recipient=recipient,
                amount=amount,
                transaction_type='TRANSFER',
                status='COMPLETED',
                reference_number=reference_number,
                description=note
            )

            # Update account balances
            request.user.account_balance -= amount
            request.user.save()

            recipient.account_balance += amount
            recipient.save()

            return JsonResponse({
                'success': True,
                'message': 'Transfer completed successfully',
                'transaction_id': transaction.reference_number
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return render(request, 'fund_transfer.html')

    

@login_required
def dashboard(request):
    """View function for the dashboard page."""
    if request.user.is_superuser:  # Redirect superuser to admin panel
        return redirect('admin_panel')
        
    # Get current user's account details
    user_account = {
        'account_number': request.user.account_number,
        'account_balance': str(request.user.account_balance),
        'full_name': f"{request.user.first_name} {request.user.last_name}",
        'email': request.user.email
    }
    
    # Get transactions
    transactions = Transaction.objects.filter(
        models.Q(sender=request.user) | models.Q(recipient=request.user)
    ).order_by('-timestamp')

    # Process transactions for display
    processed_transactions = []
    for transaction in transactions:
        is_credit = transaction.recipient == request.user
        is_debit = transaction.sender == request.user
        
        # Handle the case where sender might be None
        sender_info = "System" if transaction.sender is None else transaction.sender.account_number
        
        processed_transactions.append({
            'id': transaction.id,
            'date': transaction.timestamp.strftime('%Y-%m-%d %H:%M'),
            'amount': transaction.amount,
            'type': 'credit' if is_credit else 'debit',
            'description': transaction.description if not is_credit else f'Transfer from {sender_info}',
            'status': transaction.status if hasattr(transaction, 'status') else 'completed'
        })
    # Calculate CIBIL score
    base_score = 300
    max_score = 900
    
    # Factors that affect CIBIL score
    payment_history_score = 0
    credit_utilization_score = 0
    credit_history_score = 0
    credit_mix_score = 0
    
    # 1. Payment History (35% of score) - Max 315 points
    # Check transaction history for regular payments
    sender_transactions = Transaction.objects.filter(sender=request.user)
    if sender_transactions.count() > 5:
        payment_history_score = 200  # Good score for active users
    elif sender_transactions.count() > 0:
        payment_history_score = 150  # Medium score for some activity
    else:
        payment_history_score = 105  # Lower score for new users
        
    # Check loan repayment history if available
    try:
        loans = LoanApplication.objects.filter(client=request.user)
        if loans.exists():
            # If user has loans, adjust the score based on their status
            payment_history_score = max(payment_history_score, 200)
    except:
        # If LoanApplication model doesn't exist or other error, continue with transaction-based score
        pass
    
    # 2. Credit Utilization (30% of score) - Max 270 points
    # Calculate based on account balance
    account_balance = request.user.account_balance
    
    # Higher balance = better utilization score (simplified model)
    if account_balance > 100000:
        credit_utilization_score = 270  # Excellent
    elif account_balance > 50000:
        credit_utilization_score = 230  # Very good
    elif account_balance > 10000:
        credit_utilization_score = 200  # Good
    elif account_balance > 1000:
        credit_utilization_score = 150  # Fair
    else:
        credit_utilization_score = 100  # Poor
    
    # 3. Credit History Length (15% of score) - Max 135 points
    # Calculate based on account age
    account_age_days = (timezone.now().date() - request.user.date_joined.date()).days
    
    # 45 points per year, max 135 points (3 years)
    credit_history_score = min(135, int(account_age_days / 365 * 45))
    
    # 4. Credit Mix (20% of score) - Max 180 points
    # Check different types of transactions
    transaction_types = set()
    for transaction in sender_transactions:
        transaction_types.add(transaction.transaction_type)
    
    # Calculate credit mix score based on variety
    if len(transaction_types) >= 3:
        credit_mix_score = 180  # Excellent mix
    elif len(transaction_types) == 2:
        credit_mix_score = 120  # Good mix
    elif len(transaction_types) == 1:
        credit_mix_score = 60   # Fair mix
    else:
        credit_mix_score = 45   # Poor mix
    
    # Calculate total score
    cibil_score = base_score + payment_history_score + credit_utilization_score + credit_history_score + credit_mix_score
    cibil_score = min(max_score, cibil_score)  # Cap at max score
    
    # Determine score category
    if cibil_score >= 750:
        score_category = "Excellent credit rating"
        score_color = "success"
    elif cibil_score >= 700:
        score_category = "Good credit rating"
        score_color = "primary"
    elif cibil_score >= 650:
        score_category = "Fair credit rating"
        score_color = "warning"
    elif cibil_score >= 600:
        score_category = "Poor credit rating"
        score_color = "orange"
    else:
        score_category = "Very Poor credit rating"
        score_color = "danger"

    context = {
        'user': request.user,
        'user_account': user_account,
        'transactions': processed_transactions,
        'cibil_score': cibil_score,
        'score_category': score_category,
        'score_color': score_color
    }
    return render(request, 'dashboard.html', context)

@login_required
def admin_panel(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        User = get_user_model()
        
        # Get counts using annotate
        user_stats = User.objects.aggregate(
            total_clients=Count('id', filter=models.Q(is_superuser=False)),
            active_accounts=Count('id', filter=models.Q(is_active=True, is_superuser=False)),
            pending_accounts=Count('id', filter=models.Q(is_active=False, is_superuser=False))
        )
        
        # Get pending users
        pending_users = User.objects.filter(
            is_approved=False,
            is_pending=True,
            is_superuser=False
        )
        
        # Get pending cheque deposits
        pending_cheques = ChequeDeposit.objects.filter(status='pending').select_related('user').order_by('-deposit_date')
        
        # Get recent activities (last 10)
        recent_activities = []
        
        # Get recent transactions
        recent_transactions = Transaction.objects.select_related('sender', 'recipient').order_by('-timestamp')[:10]
        for transaction in recent_transactions:
            # Handle case where sender might be None (system transactions)
            sender_username = "System" if transaction.sender is None else transaction.sender.username
            recipient_username = "System" if transaction.recipient is None else transaction.recipient.username
            
            recent_activities.append({
                'type': 'Transaction',
                'user': sender_username,
                'action': f'Transferred ${transaction.amount} to {recipient_username}',
                'timestamp': transaction.timestamp
            })
        
        # Get recent loan applications
        recent_loans = LoanApplication.objects.select_related('user').order_by('-applied_date')[:10]
        for loan in recent_loans:
            recent_activities.append({
                'type': 'Loan Application',
                'user': loan.user.username,
                'action': f'Applied for ${loan.amount} {loan.loan_type} loan',
                'timestamp': loan.applied_date
            })
        
        # Get recent cheque deposits
        recent_cheques = ChequeDeposit.objects.select_related('user').order_by('-deposit_date')[:5]
        for cheque in recent_cheques:
            recent_activities.append({
                'type': 'Cheque Deposit',
                'user': cheque.user.username,
                'action': f'Deposited cheque for ${cheque.amount} from {cheque.bank_name}',
                'timestamp': cheque.deposit_date
            })
        
        # Sort activities by timestamp
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]  # Get most recent 10 activities
        
        context = {
            'total_clients': user_stats['total_clients'],
            'active_accounts': user_stats['active_accounts'],
            'pending_accounts': user_stats['pending_accounts'],
            'recent_activities': recent_activities,
            'pending_users': pending_users,
            'pending_cheques': pending_cheques  # Add pending cheques to context
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Exception as e:
        print(f"Error in admin_panel: {str(e)}")
        return render(request, 'admin_panel.html', {'error': str(e)})

def login_view(request):
    """View function for user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            request.session.flush()
            login(request, user)
            
            # Store user account details in session
            request.session['user_account'] = {
                'account_number': user.account_number,
                'account_balance': str(user.account_balance),
                'full_name': f"{user.first_name} {user.last_name}",
                'email': user.email
            }
            request.session.set_expiry(3600)  # 1 hour
            
            if user.is_superuser:
                return JsonResponse({'success': True, 'message': 'Login successful!', 'redirect_url': '/admin_panel/'})
            return JsonResponse({'success': True, 'message': 'Login successful!', 'redirect_url': '/dashboard/'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid username or password'})
    
    return render(request, 'loginpage.html')

@login_required
def loan_normal(request):
    return render(request, 'loan_normal.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_loan_applications(request):
    loans = LoanApplication.objects.all().order_by('-applied_date')
    loan_data = []
    
    for loan in loans:
        status_display = {
    'pending': 'Pending',
    'approved': 'Approved',
    'rejected': 'Rejected'
}.get(loan.status.lower(), loan.status)
        loan_data.append({
            'id': loan.id,
            'client_name': loan.user.get_full_name(),
            'amount': str(loan.amount),
            'purpose': loan.purpose,
    'status': status_display,  # ✅ Use formatted status
            'applied_date': loan.applied_date.strftime('%Y-%m-%d %H:%M'),
            'view_url': f'/get_loan_details/{loan.id}/'
        })
    
    return JsonResponse({'loans': loan_data})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_loan_details(request, loan_id):
    try:
        loan = LoanApplication.objects.get(id=loan_id)
        data = {
            'client_name': loan.user.get_full_name() or loan.user.username,
            'amount': str(loan.amount),
            'loan_type': loan.get_loan_type_display(),

            'purpose': loan.purpose,
            'monthly_income': str(loan.monthly_income),
            'employment_status': loan.employment_status,
            'applied_date': loan.applied_date.strftime('%Y-%m-%d %H:%M')
        }
        return JsonResponse(data)
    except LoanApplication.DoesNotExist:
        return JsonResponse({'error': 'Loan application not found'}, status=404)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def process_loan_decision(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        # Get loan data from POST or JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            loan_id = data.get('loan_id')
            decision = data.get('decision')
            notes = data.get('review_notes')
        else:
            loan_id = request.POST.get('loan_id')
            decision = request.POST.get('decision')
            notes = request.POST.get('review_notes')

        with transaction.atomic():
            loan = LoanApplication.objects.select_for_update().get(id=loan_id)
            
            # Update status based on decision
            status = 'approved' if decision.lower() == 'approve' else 'rejected'

            loan.status = status
            loan.review_notes = notes
            loan.reviewed_by = request.user
            loan.reviewed_date = timezone.now()
            loan.save()

            if status == 'approved':
                # Handle approval specific logic
                user = loan.user
                user.account_balance = F('account_balance') + loan.amount
                user.save(update_fields=['account_balance'])  # Ensure update is applied

                user.refresh_from_db()
                
                # Create transaction record
                Transaction.objects.create(
                    sender=request.user,
                    recipient=user,
                    amount=loan.amount,
                    transaction_type='LOAN_DISBURSEMENT',
                    status='COMPLETED',
                    reference_number=f'LOAN-{loan.id}'
                )
                
                # Create approval notification
                Notification.objects.create(
                    user=user,
                    message=f"Congratulations! Your loan application for ${loan.amount} has been approved!\nThe amount has been credited to your account.\nLoan Type: {loan.get_loan_type_display()}\nPurpose: {loan.purpose}",
                    notification_type='LOAN_APPROVED',
                    is_read=False
                )
            else:
                # Create rejection notification
                Notification.objects.create(
                    user=loan.user,
                    message=f"Your loan application for ${loan.amount} has been rejected.\nReason: {notes}",
                    notification_type='LOAN_REJECTED',
                    is_read=False
                )
            
            return JsonResponse({
                'success': True,
                'status': status,
                'message': f'Loan application {decision.lower()}d successfully'
            })
            
    except LoanApplication.DoesNotExist:
        return JsonResponse({'error': 'Loan application not found'}, status=404)
    except Exception as e:
        print(f"Error in process_loan_decision: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def process_loan_application(request):
    if request.method == 'POST':
        try:
            # Get form data
            amount = Decimal(request.POST.get('amount'))
            monthly_income = Decimal(request.POST.get('monthly_income'))
            employment_status = request.POST.get('employment_status')
            loan_type = request.POST.get('loan_type')
            purpose = request.POST.get('purpose')
            
            # Create loan application
            loan = LoanApplication.objects.create(
                client=request.user,
                loan_type=loan_type,
                amount=amount,
                purpose=purpose,
                monthly_income=monthly_income,
                employment_status=employment_status,
                
                status='PENDING',
                is_approved=False
            )
            
            # Create notification for admin
            admin_users = get_user_model().objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    message=f"New loan application from {request.user.get_full_name() or request.user.username} for {loan.get_loan_type_display()} of ${amount}",
                    notification_type="LOAN_APPROVED"
                )
            
            # Create notification for user
            Notification.objects.create(
                user=request.user,
                message=f"Your loan application for {loan.get_loan_type_display()} of ${amount} has been submitted and is pending review.",
                notification_type="LOAN_APPROVED"
            )
            
            messages.success(request, "Loan application submitted successfully! You will be notified once it's reviewed.")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Error submitting loan application: {str(e)}")
            return redirect('loan')
    
    # If not POST, redirect to loan page
    return redirect('loan')

@login_required
def submit_loan_application(request):
    if request.method == 'POST':
        try:
            # Get form data
            amount = Decimal(request.POST.get('amount'))
            monthly_income = Decimal(request.POST.get('monthly_income'))
            employment_status = request.POST.get('employment_status')
            loan_type = request.POST.get('loan_type', 'personal')
            purpose = request.POST.get('purpose')
            
            # Create loan application using user instead of client
            loan = LoanApplication.objects.create(
                user=request.user,  # Changed from client to user
                loan_type=loan_type,
                amount=amount,
                purpose=purpose,
                monthly_income=monthly_income,
                employment_status=employment_status,
                status='pending',
                # Add client information from the user model
                client_name=f"{request.user.first_name} {request.user.last_name}",
                client_email=request.user.email,
                client_phone=request.user.phone_number,
                client_address=request.user.address
            )
            
            # Rest of your notification code remains the same
            
            # Create notification for admin
            admin_users = get_user_model().objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    message=f"New loan application from {request.user.get_full_name() or request.user.username} for {loan_type} of${amount}",
                    notification_type="LOAN_APPLICATION"
                )
            
            # Create notification for user
            Notification.objects.create(
                user=request.user,
                message=f"Your loan application for {loan_type} of ${amount} has been submitted and is pending review.",
                notification_type="LOAN_APPLICATION"
            )
            
            # Return success response
            return JsonResponse({
                'success': True, 
                'message': 'Your loan application has been sent to the admin for review.'
            })
            
        except Exception as e:
            print(f"Error in submit_loan_application: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error submitting loan application: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_loan_applications(request):
    loans = LoanApplication.objects.all().order_by('-applied_date')
    loan_data = []
    
    for loan in loans:
        # Get proper status display
        status_display = {
    'pending': 'Pending',
    'approved': 'Approved',
    'rejected': 'Rejected'
}.get(loan.status.lower(), loan.status)

        
        loan_data.append({
            'id': loan.id,
            'client_name': loan.user.get_full_name() or loan.user.username,
            'amount': str(loan.amount),
            'loan_type': loan.loan_type,
            'purpose': loan.purpose,
            'employment_status': loan.employment_status,
            'status': status_display,  # Use the formatted status
            'applied_date': loan.applied_date.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({'loans': loan_data})

@login_required
def get_notifications(request):
    try:
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]  # Get last 10 notifications
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'notification_type': notification.notification_type
            })
        
        return JsonResponse({'notifications': notifications_data})
    except Exception as e:
        print(f"Error in get_notifications: {str(e)}")  # Server-side logging
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        try:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def get_recent_activities(request):
    try:
        # Get recent transactions
        recent_transactions = Transaction.objects.select_related('sender', 'recipient').order_by('-timestamp')[:10]
        
        # Get recent loan applications
        recent_loans = LoanApplication.objects.select_related('user').order_by('-applied_date')[:10]
        
        activities = []
        
        # Add transactions to activities
        for transaction in recent_transactions:
            # Handle cases where sender or recipient might be None
            sender_name = "System" if transaction.sender is None else transaction.sender.username
            recipient_name = "System" if transaction.recipient is None else transaction.recipient.username
            
            activities.append({
                'type': 'Transaction',
                'user': sender_name,
                'action': f'Transferred ${transaction.amount} to {recipient_name}',
                'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Add loan applications to activities
        for loan in recent_loans:
            # Handle case where user might be None
            user_name = "Unknown User" if loan.user is None else loan.user.username
            
            activities.append({
                'type': 'Loan Application',
                'user': user_name,
                'action': f'Applied for ${loan.amount} {loan.loan_type} loan',
                'timestamp': loan.applied_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:10]  # Get most recent 10 activities
        
        return JsonResponse({'activities': activities})
        
    except Exception as e:
        print(f"Error in get_recent_activities: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

def transaction_data(request):
    try:
        # Get last 30 days of transactions
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        transactions = Transaction.objects.filter(
            timestamp__range=[start_date, end_date]
        ).values('timestamp__date').annotate(
            amount=Sum('amount')
        ).order_by('timestamp__date')
        
        data = [{
            'date': transaction['timestamp__date'].strftime('%Y-%m-%d'),
            'amount': float(transaction['amount'])
        } for transaction in transactions]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_transaction_volume(request):
    try:
        days = int(request.GET.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get transactions for the selected period
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )

        # Initialize data dictionaries
        daily_amounts = defaultdict(float)
        daily_counts = defaultdict(int)

        # Aggregate data by date
        for transaction in transactions:
            date_str = transaction.timestamp.strftime('%Y-%m-%d')
            daily_amounts[date_str] += float(transaction.amount)
            daily_counts[date_str] += 1

        # Generate date range
        date_range = []
        amounts = []
        counts = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_range.append(date_str)
            amounts.append(daily_amounts.get(date_str, 0))
            counts.append(daily_counts.get(date_str, 0))
            current_date += timedelta(days=1)

        return JsonResponse({
            'labels': date_range,
            'amounts': amounts,
            'counts': counts
        })

    except Exception as e:
        print(f"Error in get_transaction_volume: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_admin_stats(request):
    try:
        User = get_user_model()
        now = timezone.now()
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Get user statistics
        user_stats = User.objects.aggregate(
            total_clients=Count('id', filter=Q(is_superuser=False, is_staff=False)),
            active_accounts=Count('id', filter=Q(is_active=True, is_superuser=False, is_staff=False)),
            pending_accounts=Count('id', filter=Q(is_active=False, is_superuser=False, is_staff=False))
        )

        # Get 24-hour transaction data
        transactions_24h = Transaction.objects.filter(
            timestamp__gte=twenty_four_hours_ago
        ).aggregate(
            total_amount=Sum('amount'),
            count=Count('id')
        )

        # Get total transaction data
        total_transactions = Transaction.objects.aggregate(
            total_amount=Sum('amount'),
            count=Count('id')
        )

        return JsonResponse({
            'total_clients': user_stats['total_clients'] or 0,
            'active_accounts': user_stats['active_accounts'] or 0,
            'pending_accounts': user_stats['pending_accounts'] or 0,
            'transactions_24h': float(transactions_24h['total_amount'] or 0),
            'transactions_count': transactions_24h['count'] or 0,
            'total_transactions': float(total_transactions['total_amount'] or 0),
            'total_transactions_count': total_transactions['count'] or 0
        })

    except Exception as e:
        print(f"Error in get_admin_stats: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def download_transaction_report(request):
    try:
        days = int(request.GET.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get detailed transactions
        transactions = Transaction.objects.select_related('sender', 'recipient').filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('-timestamp')

        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transaction_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        # Create CSV writer
        writer = csv.writer(response)
        writer.writerow([
            'Transaction Date',
            'Transaction ID',
            'Sender',
            'Recipient',
            'Amount ($)',
            'Transaction Type',
            'Status'
        ])

        # Write transaction data
        for transaction in transactions:
            writer.writerow([
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                transaction.id,
                transaction.sender.username,
                transaction.recipient.username,
                f"{transaction.amount:.2f}",
                transaction.transaction_type,
                transaction.status
            ])

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_transaction_volume(request):
    try:
        days = int(request.GET.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get transactions for the selected period
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')

        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transaction_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        # Create CSV writer
        writer = csv.writer(response)
        writer.writerow(['Date', 'Transaction Amount', 'Number of Transactions'])

        # Aggregate data by date
        daily_data = defaultdict(lambda: {'amount': 0, 'count': 0})
        
        for transaction in transactions:
            date_str = transaction.timestamp.strftime('%Y-%m-%d')
            daily_data[date_str]['amount'] += float(transaction.amount)
            daily_data[date_str]['count'] += 1

        # Write data rows
        for date_str in sorted(daily_data.keys()):
            writer.writerow([
                date_str,
                f"${daily_data[date_str]['amount']:.2f}",
                daily_data[date_str]['count']
            ])

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            if action == 'approve':
                user.is_active = True
                user.is_approved = True
                user.save()
                
                # Create a notification for the user
                Notification.objects.create(
                    user=user,
                    message="Your account has been approved. You can now log in and use all banking features.",
                    notification_type="ACCOUNT"
                )
                
                return JsonResponse({'status': 'success', 'message': f'User {user.username} has been approved'})
            
            elif action == 'reject':
                # Optionally store rejected user info before deletion
                username = user.username
                user.delete()
                return JsonResponse({'status': 'success', 'message': f'User {username} has been rejected'})
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'})
                
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def cibil_score(request):
    """
    View to display and calculate the user's CIBIL score.
    CIBIL score is calculated based on credit history, loan repayment, and account activity.
    """
    try:
        # Get the current user
        user = request.user
        
        # Check if we should use existing CIBIL score or recalculate
        refresh = request.GET.get('refresh', 'false').lower() == 'true'
        
        # Initialize variables for CIBIL score calculation
        base_score = 300
        max_score = 900
        
        # Factors that affect CIBIL score
        payment_history_score = 0
        credit_utilization_score = 0
        credit_history_score = 0
        credit_mix_score = 0
        
        # 1. Payment History (35% of score) - Max 315 points
        # Check transaction history for regular payments
        transactions = Transaction.objects.filter(sender=user)
        if transactions.count() > 5:
            payment_history_score = 200  # Good score for active users
        elif transactions.count() > 0:
            payment_history_score = 150  # Medium score for some activity
        else:
            payment_history_score = 105  # Lower score for new users
            
        # Check loan repayment history if available
        try:
            loans = LoanApplication.objects.filter(client=user)
            if loans.exists():
                # If user has loans, adjust the score based on their status
                payment_history_score = max(payment_history_score, 200)
        except:
            # If LoanApplication model doesn't exist or other error, continue with transaction-based score
            pass
        
        # 2. Credit Utilization (30% of score) - Max 270 points
        # Calculate based on account balance
        account_balance = user.account_balance
        
        # Higher balance = better utilization score (simplified model)
        if account_balance > 100000:
            credit_utilization_score = 270  # Excellent
        elif account_balance > 50000:
            credit_utilization_score = 230  # Very good
        elif account_balance > 10000:
            credit_utilization_score = 200  # Good
        elif account_balance > 1000:
            credit_utilization_score = 150  # Fair
        else:
            credit_utilization_score = 100  # Poor
        
        # 3. Credit History Length (15% of score) - Max 135 points
        # Calculate based on account age
        account_age_days = (timezone.now().date() - user.date_joined.date()).days
        
        # 45 points per year, max 135 points (3 years)
        credit_history_score = min(135, int(account_age_days / 365 * 45))
        
        # 4. Credit Mix (20% of score) - Max 180 points
        # Check different types of transactions
        transaction_types = set()
        for transaction in transactions:
            transaction_types.add(transaction.transaction_type)
        
        # Calculate credit mix score based on variety
        if len(transaction_types) >= 3:
            credit_mix_score = 180  # Excellent mix
        elif len(transaction_types) == 2:
            credit_mix_score = 120  # Good mix
        elif len(transaction_types) == 1:
            credit_mix_score = 60   # Fair mix
        else:
            credit_mix_score = 45   # Poor mix
        
        # Calculate total score
        score = base_score + payment_history_score + credit_utilization_score + credit_history_score + credit_mix_score
        score = min(max_score, score)  # Cap at max score
        
        # Calculate percentages for progress bars
        payment_history_percentage = (payment_history_score / 315) * 100
        credit_utilization_percentage = (credit_utilization_score / 270) * 100
        credit_history_percentage = (credit_history_score / 135) * 100
        credit_mix_percentage = (credit_mix_score / 180) * 100
        
        # Determine score category and color
        if score >= 750:
            score_category = "Excellent"
            score_color = "success"
            score_description = "You have an excellent credit score. You're likely to get approved for loans with the best interest rates."
        elif score >= 700:
            score_category = "Good"
            score_color = "primary"
            score_description = "You have a good credit score. You're likely to qualify for most loans with competitive interest rates."
        elif score >= 650:
            score_category = "Fair"
            score_color = "warning"
            score_description = "You have a fair credit score. You may qualify for loans but with higher interest rates."
        elif score >= 600:
            score_category = "Poor"
            score_color = "orange"
            score_description = "You have a poor credit score. You may face difficulty getting approved for loans."
        else:
            score_category = "Very Poor"
            score_color = "danger"
            score_description = "You have a very poor credit score. You'll likely face significant challenges getting approved for credit."
        
        # Generate score history data (last 6 months)
        score_history = []
        current_date = timezone.now().date()
        current_score = score
        
        for i in range(6, -1, -1):
            month_date = current_date - timedelta(days=30*i)
            # Simulate some random fluctuation in historical scores
            if i > 0:  # Not the current score
                historical_score = max(300, min(900, current_score - random.randint(-15, 20)))
            else:
                historical_score = current_score
                
            score_history.append({
                'date': month_date.strftime('%b %Y'),
                'score': historical_score
            })
        
        # Debug prints to help diagnose issues
        print(f"DEBUG - CIBIL Score: {score}")
        print(f"DEBUG - Payment History: {payment_history_score}")
        print(f"DEBUG - Credit Utilization: {credit_utilization_score}")
        print(f"DEBUG - Credit History: {credit_history_score}")
        print(f"DEBUG - Credit Mix: {credit_mix_score}")
        
        context = {
            'score': score,
            'max_score': max_score,
            'score_category': score_category,
            'score_color': score_color,
            'score_description': score_description,
            'payment_history_score': payment_history_score,
            'payment_history_percentage': payment_history_percentage,
            'credit_utilization_score': credit_utilization_score,
            'credit_utilization_percentage': credit_utilization_percentage,
            'credit_history_score': credit_history_score,
            'credit_history_percentage': credit_history_percentage,
            'credit_mix_score': credit_mix_score,
            'credit_mix_percentage': credit_mix_percentage,
            'score_history': json.dumps(score_history),
            'now': timezone.now(),
        }
        
        return render(request, 'cibil_score.html', context)
    
    except Exception as e:
        print(f"CIBIL Score Error: {str(e)}")  # Add this for debugging
        context = {
            'error': str(e)
        }
        return render(request, 'cibil_score.html', context)
@login_required
def get_cibil_data(request):
    """
    API endpoint to fetch the current user's CIBIL score data for loan applications
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        })
    
    try:
        # Get the current user
        user = request.user
        
        # Calculate CIBIL score directly (similar to cibil_score view)
        base_score = 300
        max_score = 900
        
        # Factors that affect CIBIL score
        payment_history_score = 0
        credit_utilization_score = 0
        credit_history_score = 0
        credit_mix_score = 0
        
        # 1. Payment History (35% of score) - Max 315 points
        transactions = Transaction.objects.filter(sender=user)
        if transactions.count() > 5:
            payment_history_score = 200
        elif transactions.count() > 0:
            payment_history_score = 150
        else:
            payment_history_score = 105
            
        # Check loan repayment history
        try:
            loans = LoanApplication.objects.filter(client=user)
            if loans.exists():
                payment_history_score = max(payment_history_score, 200)
        except:
            pass
        
        # 2. Credit Utilization (30% of score) - Max 270 points
        account_balance = user.account_balance
        
        if account_balance > 100000:
            credit_utilization_score = 270
        elif account_balance > 50000:
            credit_utilization_score = 230
        elif account_balance > 10000:
            credit_utilization_score = 200
        elif account_balance > 1000:
            credit_utilization_score = 150
        else:
            credit_utilization_score = 100
        
        # 3. Credit History Length (15% of score) - Max 135 points
        account_age_days = (timezone.now().date() - user.date_joined.date()).days
        credit_history_score = min(135, int(account_age_days / 365 * 45))
        
        # 4. Credit Mix (20% of score) - Max 180 points
        transaction_types = set()
        for transaction in transactions:
            transaction_types.add(transaction.transaction_type)
        
        if len(transaction_types) >= 3:
            credit_mix_score = 180
        elif len(transaction_types) == 2:
            credit_mix_score = 120
        elif len(transaction_types) == 1:
            credit_mix_score = 60
        else:
            credit_mix_score = 45
        
        # Calculate total score
        score = base_score + payment_history_score + credit_utilization_score + credit_history_score + credit_mix_score
        score = min(max_score, score)  # Cap at max score
        
        # Determine score category
        if score >= 750:
            score_category = "Excellent"
        elif score >= 700:
            score_category = "Good"
        elif score >= 650:
            score_category = "Fair"
        elif score >= 600:
            score_category = "Poor"
        else:
            score_category = "Very Poor"
        
        # Log the calculated score for debugging
        print(f"Calculated CIBIL score for {user.username}: {score}")
        
        # Return CIBIL data as JSON
        return JsonResponse({
            'success': True,
            'data': {
                'score': score,
                'score_category': score_category,
                'personal_loan_status': 'Eligible' if score >= 700 else ('Conditionally Eligible' if score >= 650 else 'Not Eligible'),
                'home_loan_status': 'Eligible' if score >= 700 else ('Conditionally Eligible' if score >= 650 else 'Not Eligible'),
                'car_loan_status': 'Eligible' if score >= 700 else ('Conditionally Eligible' if score >= 650 else 'Not Eligible'),
                'personal_loan_rate': '10.5% - 12.5%' if score >= 750 else ('12.5% - 14.5%' if score >= 700 else ('14.5% - 16.5%' if score >= 650 else '16.5%+')),
                'home_loan_rate': '6.5% - 7.5%' if score >= 750 else ('7.5% - 8.5%' if score >= 700 else ('8.5% - 9.5%' if score >= 650 else '9.5%+')),
                'car_loan_rate': '7.5% - 8.5%' if score >= 750 else ('8.5% - 9.5%' if score >= 700 else ('9.5% - 10.5%' if score >= 650 else '10.5%+'))
            }
        })
    except Exception as e:
        print(f"Error in get_cibil_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
def get_cibil_data(request, user_id):
    try:
        cibil = CibilScore.objects.get(user_id=user_id)
        data = {
            "cibil_score": cibil.score,
            "eligibility": cibil.eligibility,
            "interest_rate": cibil.interest_rate
        }
        return JsonResponse(data)
    except CibilScore.DoesNotExist:
        return JsonResponse({"error": "CIBIL data not found"}, status=404)

@login_required
def refresh_cibil_score(request):
    """API endpoint to refresh CIBIL score"""
    try:
        # Redirect to the cibil_score view with refresh parameter
        return redirect(reverse('cibil_score') + '?refresh=true')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_cibil_eligibility(request):
    user = request.user
    
    try:
        # Get the user's CIBIL score from the database
        cibil_score = CibilScore.objects.get(user=user)
        
        # Return the data as JSON
        return JsonResponse({
            'score': cibil_score.score,
            'eligibility': cibil_score.eligibility,
            'interest_rate': cibil_score.interest_rate
        })
    except CibilScore.DoesNotExist:
        # If no CIBIL score exists, create a default one with calculated values
        cibil_score = CibilScore(user=user)
        cibil_score.save()  # This will trigger the save method that calculates eligibility
        
        return JsonResponse({
            'score': cibil_score.score,
            'eligibility': cibil_score.eligibility,
            'interest_rate': cibil_score.interest_rate
        })

@login_required
def get_user_loan_eligibility(request):
    """API endpoint to get loan eligibility data for the current user"""
    try:
        # Calculate CIBIL score (similar to cibil_score view)
        user = request.user
        
        # Calculate CIBIL score directly (similar to cibil_score view)
        base_score = 300
        max_score = 900
        
        # Factors that affect CIBIL score
        payment_history_score = 0
        credit_utilization_score = 0
        credit_history_score = 0
        credit_mix_score = 0
        
        # 1. Payment History (35% of score) - Max 315 points
        transactions = Transaction.objects.filter(sender=user)
        if transactions.count() > 5:
            payment_history_score = 200
        elif transactions.count() > 0:
            payment_history_score = 150
        else:
            payment_history_score = 105
            
        # Check loan repayment history
        try:
            loans = LoanApplication.objects.filter(client=user)
            if loans.exists():
                payment_history_score = max(payment_history_score, 200)
        except:
            pass
        
        # 2. Credit Utilization (30% of score) - Max 270 points
        account_balance = user.account_balance
        
        if account_balance > 100000:
            credit_utilization_score = 270
        elif account_balance > 50000:
            credit_utilization_score = 230
        elif account_balance > 10000:
            credit_utilization_score = 200
        elif account_balance > 1000:
            credit_utilization_score = 150
        else:
            credit_utilization_score = 100
        
        # 3. Credit History Length (15% of score) - Max 135 points
        account_age_days = (timezone.now().date() - user.date_joined.date()).days
        credit_history_score = min(135, int(account_age_days / 365 * 45))
        
        # 4. Credit Mix (20% of score) - Max 180 points
        transaction_types = set()
        for transaction in transactions:
            transaction_types.add(transaction.transaction_type)
        
        if len(transaction_types) >= 3:
            credit_mix_score = 180
        elif len(transaction_types) == 2:
            credit_mix_score = 120
        elif len(transaction_types) == 1:
            credit_mix_score = 60
        else:
            credit_mix_score = 45
        
        # Calculate total score
        score = base_score + payment_history_score + credit_utilization_score + credit_history_score + credit_mix_score
        score = min(max_score, score)  # Cap at max score
        
        # Determine loan eligibility based on score
        # For this example, we'll use a simple threshold-based approach
        if score < 600:  # Very Poor
            loan_eligibility = [
                {"type": "Personal Loan", "status": "Not Eligible", "interest_rate": "16.5%+"},
                {"type": "Home Loan", "status": "Not Eligible", "interest_rate": "9.5%+"},
                {"type": "Car Loan", "status": "Not Eligible", "interest_rate": "10.5%+"}
            ]
        elif score < 650:  # Poor
            loan_eligibility = [
                {"type": "Personal Loan", "status": "Not Eligible", "interest_rate": "16.5%+"},
                {"type": "Home Loan", "status": "Not Eligible", "interest_rate": "9.5%+"},
                {"type": "Car Loan", "status": "Not Eligible", "interest_rate": "10.5%+"}
            ]
        elif score < 700:  # Fair
            loan_eligibility = [
                {"type": "Personal Loan", "status": "Conditionally Eligible", "interest_rate": "14.5% - 16.5%"},
                {"type": "Home Loan", "status": "Conditionally Eligible", "interest_rate": "8.5% - 9.5%"},
                {"type": "Car Loan", "status": "Conditionally Eligible", "interest_rate": "9.5% - 10.5%"}
            ]
        elif score < 750:  # Good
            loan_eligibility = [
                {"type": "Personal Loan", "status": "Eligible", "interest_rate": "12.5% - 14.5%"},
                {"type": "Home Loan", "status": "Eligible", "interest_rate": "7.5% - 8.5%"},
                {"type": "Car Loan", "status": "Eligible", "interest_rate": "8.5% - 9.5%"}
            ]
        else:  # Excellent
            loan_eligibility = [
                {"type": "Personal Loan", "status": "Eligible", "interest_rate": "10.5% - 12.5%"},
                {"type": "Home Loan", "status": "Eligible", "interest_rate": "6.5% - 7.5%"},
                {"type": "Car Loan", "status": "Eligible", "interest_rate": "7.5% - 8.5%"}
            ]
        
        # Return the loan eligibility data
        return JsonResponse({
            'success': True,
            'cibil_score': score,
            'loan_eligibility': loan_eligibility
        })
    except Exception as e:
        print(f"Error in get_user_loan_eligibility: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def get_transaction_data(request):
    try:
        # Get current month and year
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Get all transactions for the current user (both sent and received)
        sent_transactions = Transaction.objects.filter(
            sender=request.user,
            timestamp__month=current_month,
            timestamp__year=current_year
        ).order_by('-timestamp')
        
        received_transactions = Transaction.objects.filter(
            recipient=request.user,
            timestamp__month=current_month,
            timestamp__year=current_year
        ).order_by('-timestamp')
        
        all_transactions = list(sent_transactions) + list(received_transactions)
        all_transactions.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Format the data for the frontend
        formatted_transactions = []
        category_totals = {
            'Utilities': 0,
            'Food': 0,
            'Dining': 0,
            'Transportation': 0,
            'Shopping': 0,
            'Educational': 0,
            'Income': 0,
            'Uncategorized': 0
        }
        
        # Monthly data for the chart
        monthly_data = {
            'labels': [timezone.now().strftime('%b %Y')],
            'income': [0],
            'expenses': [0]
        }
        
        total_income = 0
        total_expense = 0
        
        # Process each transaction
        for transaction in all_transactions:
            is_expense = transaction.sender == request.user
            amount = float(transaction.amount)
            
            # Update totals
            if is_expense:
                total_expense += amount
                monthly_data['expenses'][0] += amount
            else:
                total_income += amount
                monthly_data['income'][0] += amount
            
            # Categorize transaction
            category = 'Uncategorized'
            description = transaction.description.lower() if transaction.description else ''
            
            if not is_expense:
                category = 'Income'
            elif 'bill' in description or 'utility' in description:
                category = 'Utilities'
            elif 'grocery' in description or 'food' in description:
                category = 'Food'
            elif 'restaurant' in description or 'cafe' in description:
                category = 'Dining'
            elif 'gas' in description or 'transport' in description:
                category = 'Transportation'
            elif 'shopping' in description or 'store' in description:
                category = 'Shopping'
            elif 'fees' in description or 'stationary' in description:
                category = 'Educational'
            
            # Add to formatted transactions - include both credit and debit transactions
            formatted_transactions.append({
                'date': transaction.timestamp.strftime('%b %d, %Y'),
                'description': transaction.description or 'Transaction',
                'amount': amount,
                'category': category,
                'transaction_type': 'credit' if not is_expense else 'debit'
            })
            
            # Update category totals
            if is_expense:
                category_totals[category] += amount
            else:
                category_totals['Income'] += amount
        
        # Prepare category data for pie chart
        categories_data = [
            {'category': cat, 'amount': float(amount)} 
            for cat, amount in category_totals.items()
            if amount > 0 and cat != 'Income'
        ]
        
        return JsonResponse({
            'success': True,
            'transactions': formatted_transactions,  # Include all transactions
            'categories': categories_data,
            'total_income': total_income,
            'total_expense': total_expense,
            'monthly_data': monthly_data
        })
        
    except Exception as e:
        print(f"Error in get_transaction_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
        
@login_required
def spending_overview(request):
    try:
        # Get all transactions for the current user
        sent_transactions = Transaction.objects.filter(sender=request.user)
        received_transactions = Transaction.objects.filter(recipient=request.user)
        
        # Calculate totals
        total_income = received_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_expenses = sent_transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Get monthly breakdown
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Get monthly transactions (both sent and received)
        monthly_sent = Transaction.objects.filter(
            sender=request.user,
            timestamp__month=current_month,
            timestamp__year=current_year
        ).order_by('-timestamp')
        
        monthly_received = Transaction.objects.filter(
            recipient=request.user,
            timestamp__month=current_month,
            timestamp__year=current_year
        ).order_by('-timestamp')
        
        # Calculate monthly totals
        monthly_income = monthly_received.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        monthly_expenses = monthly_sent.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Prepare chart data
        chart_data = {
            'labels': ['Income', 'Expenses'],
            'datasets': [
                {
                    'label': 'Monthly Overview',
                    'data': [float(monthly_income), float(monthly_expenses)],
                    'backgroundColor': ['#36a2eb', '#ff6384']
                }
            ]
        }
        
        # Categorize expenses for pie chart
        category_totals = {
            'Utilities': 0,
            'Food': 0,
            'Dining': 0,
            'Transportation': 0,
            'Shopping': 0,
            'Educational': 0,
            'Uncategorized': 0
        }
        
        # Process each transaction for categorization
        for transaction in monthly_sent:
            description = transaction.description.lower() if transaction.description else ''
            category = 'Uncategorized'
            
            if 'bill' in description or 'utility' in description:
                category = 'Utilities'
            elif 'grocery' in description or 'food' in description:
                category = 'Food'
            elif 'restaurant' in description or 'cafe' in description:
                category = 'Dining'
            elif 'gas' in description or 'transport' in description:
                category = 'Transportation'
            elif 'shopping' in description or 'store' in description:
                category = 'Shopping'
            elif 'fees' in description or 'stationary' in description:
                category = 'Educational'
            
            category_totals[category] += float(transaction.amount)
        
        # Prepare category data for pie chart
        categories_data = [
            {'category': cat, 'amount': amount} 
            for cat, amount in category_totals.items()
            if amount > 0
        ]
        
        # Combine and sort all monthly transactions
        all_monthly_transactions = list(monthly_sent) + list(monthly_received)
        all_monthly_transactions.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Format transactions for display
        formatted_transactions = []
        for transaction in all_monthly_transactions:
            is_credit = transaction.recipient == request.user
            
            # Get other party username safely
            if is_credit:
                other_party = transaction.sender.username if transaction.sender else "Unknown"
            else:
                other_party = transaction.recipient.username if transaction.recipient else "Unknown"
                
            formatted_transactions.append({
                'date': transaction.timestamp,
                'description': transaction.description or 'Transaction',
                'amount': float(transaction.amount),
                'is_credit': is_credit,
                'transaction_type': 'credit' if is_credit else 'debit',
                'reference': transaction.reference_number,
                'other_party': other_party
            })

        import json
        context = {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'monthly_income': float(monthly_income),
            'monthly_expenses': float(monthly_expenses),
            'monthly_transactions': formatted_transactions,
            'current_month': timezone.now().strftime('%B %Y'),
            'net_balance': float(total_income - total_expenses),
            'chart_data': json.dumps(chart_data),
            'categories_data': json.dumps(categories_data)
        }
        
        return render(request, 'spending_overview.html', context)
    except Exception as e:
        print(f"Error in spending_overview: {str(e)}")
        return render(request, 'spending_overview.html', {'error': str(e)})



from django.urls import reverse
from django.db import OperationalError

@login_required
def quick_transfer(request):
    # Get recent transfers for both GET and POST requests
    recent_transfers = Transaction.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('recipient').order_by('-timestamp')[:5]
    
    if request.method == 'POST':
        try:
            recipient_account = request.POST.get('recipient_account')
            amount = request.POST.get('amount')
            description = request.POST.get('description', '')

            if not recipient_account or not amount:
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })

            try:
                amount = Decimal(amount)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid amount format'
                })

            try:
                # Get the correct User model
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Add timeout to prevent indefinite locks
                with transaction.atomic(using='default', savepoint=True):
                    recipient = User.objects.select_for_update(nowait=True).get(account_number=recipient_account)
                    sender = User.objects.select_for_update(nowait=True).get(id=request.user.id)

                    if sender.account_balance >= amount:
                        # Generate reference number
                        timestamp = int(time.time())
                        reference_number = f"{timestamp}{get_random_string(16).upper()}"

                        # Create transaction
                        new_transaction = Transaction.objects.create(
                            sender=sender,
                            recipient=recipient,
                            amount=amount,
                            description=description,
                            transaction_type='transfer',
                            reference_number=reference_number
                        )

                        # Update balances
                        sender.account_balance -= amount
                        sender.save()
                        recipient.account_balance += amount
                        recipient.save()

                        return JsonResponse({
                            'success': True,
                            'message': 'Transfer successful',
                            'new_balance': float(sender.account_balance),
                            'redirect': reverse('dashboard')
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'Insufficient balance'
                        })

            except OperationalError:
                return JsonResponse({
                    'success': False,
                    'message': 'Transaction temporarily unavailable. Please try again.'
                })
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Recipient account not found'
                })

        except Exception as e:
            print(f"Error in quick_transfer: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during transfer'
            })

    # For GET requests or after processing POST
    context = {
        'recent_transfers': recent_transfers
    }
    return render(request, 'quick_transfer.html', context)


@login_required
def validate_recipient(request, account_number):
    try:
        # Don't allow transfers to self
        if request.user.account_number == account_number:
            return JsonResponse({
                'valid': False,
                'message': 'Cannot transfer to your own account'
            })

        recipient = User.objects.get(account_number=account_number)
        
        # Check if recipient account is active
        if not recipient.is_active:
            return JsonResponse({
                'valid': False,
                'message': 'This account is not active'
            })

        return JsonResponse({
            'valid': True,
            'name': recipient.get_full_name() or recipient.username,
            'message': 'Valid recipient account'
        })
    except User.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Account number not found'
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': 'Error validating account'
        })

@login_required
def get_recipient_name(request):
    try:
        account_number = request.GET.get('account')
        print(f"Searching for account: {account_number}")
        
        if not account_number:
            return JsonResponse({
                'success': False,
                'message': 'Account number is required'
            })

        # Use get_user_model() to get the correct User model
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try direct get() instead of filter().first()
        try:
            recipient = User.objects.get(account_number=account_number)
            print(f"Found recipient: {recipient.username}")  # Debug print

            if not recipient.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'This account is not active'
                })
            
            if recipient == request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot transfer to your own account'
                })

            # Return more detailed recipient info
            response_data = {
                'success': True,
                'name': recipient.get_full_name() or recipient.username,
                'email': recipient.email,
                'account_number': recipient.account_number,
                'message': 'Valid recipient account',
                'is_active': recipient.is_active,
                'username': recipient.username
            }
            print(f"Sending response: {response_data}")  # Debug print
            return JsonResponse(response_data)

        except User.DoesNotExist:
            print(f"No user found with account number: {account_number}")  # Debug print
            return JsonResponse({
                'success': False,
                'message': f'Account number {account_number} not found'
            }, status=404)
            
    except Exception as e:
        print(f"Error in get_recipient_name: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error validating account',
            'error_details': str(e)
        }, status=500)


@login_required
def process_quick_transfer(request):
    if request.method == 'POST':
        try:
            recipient_account = request.POST.get('recipient_account')
            amount = request.POST.get('amount')
            description = request.POST.get('description', '')

            if not recipient_account or not amount:
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })

            amount = Decimal(amount)
            
            with transaction.atomic():
                recipient = User.objects.select_for_update().get(account_number=recipient_account)
                sender = User.objects.select_for_update().get(id=request.user.id)

                if sender.account_balance >= amount:
                    # Process transfer
                    timestamp = int(time.time())
                    reference_number = f"{timestamp}{get_random_string(16).upper()}"
                    
                    Transaction.objects.create(
                        sender=sender,
                        recipient=recipient,
                        amount=amount,
                        description=description,
                        transaction_type='transfer',
                        reference_number=reference_number
                    )

                    sender.account_balance -= amount
                    sender.save()
                    recipient.account_balance += amount
                    recipient.save()

                    return JsonResponse({
                        'success': True,
                        'message': 'Transfer successful',
                        'new_balance': float(sender.account_balance)
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Insufficient balance'
                    })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required
def cheque_deposit(request):
    # Debug: Print model fields
    from django.apps import apps
    model = apps.get_model('core', 'ChequeDeposit')
    print("ChequeDeposit fields:", [f.name for f in model._meta.get_fields()])
    
    if request.method == 'POST':
        try:
            # Extract form data
            amount = request.POST.get('amount')
            cheque_number = request.POST.get('cheque_number')
            bank_name = request.POST.get('bank_name')
            date_of_issue = request.POST.get('date_of_issue')
            
            # Check if this is a loan payment
            account_type = request.POST.get('account_type')
            account_id = request.POST.get('account_id')
            is_loan_payment = account_type == 'loan'
            
            # Handle file upload
            cheque_image = request.FILES.get('cheque_image')
            
            # Create a new ChequeDeposit record
            deposit = ChequeDeposit.objects.create(
                user=request.user,
                amount=Decimal(amount),
                cheque_number=cheque_number,
                bank_name=bank_name,
                date_of_issue=date_of_issue,
                front_image=cheque_image,
                status='pending',
                # Add branch_name and payee_name with default values
                branch_name='',
                payee_name=request.user.get_full_name() or request.user.username
            )
            
            # Schedule the automatic approval after 1 minute
            print(f"DEBUG: Scheduling auto approval for cheque {deposit.id}, user {request.user.id}, amount {amount} in 1 minute")
            
            # If this is a loan payment, use the loan payment approval function
            if is_loan_payment and account_id:
                from .utils import schedule_loan_payment_approval
                schedule_loan_payment_approval(deposit.id, request.user.id, amount, account_id)
                
                # Create notification for the user about loan payment
                Notification.objects.create(
                    user=request.user,
                    message=f"Your cheque deposit of ${amount} for loan payment has been received and will be processed within 1 minute.",
                    notification_type='transaction'
                )
            else:
                # Regular deposit processing
                from .utils import schedule_auto_approval
                schedule_auto_approval(deposit.id, request.user.id, amount)
                
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    message=f"Your cheque deposit of ${amount} has been received and will be processed within 1 minute.",
                    notification_type='transaction'
                )
            
            # Log the created deposit
            print(f"Created cheque deposit with ID: {deposit.id}")
            
            # Return success response with deposit ID
            return JsonResponse({
                'success': True,
                'message': 'Cheque deposit submitted successfully! It will be processed within 1 minute.',
                'deposit_id': deposit.id,
                'is_loan_payment': is_loan_payment
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
 
    return render(request, 'cheque_deposit.html')
@login_required
@user_passes_test(lambda u: u.is_superuser)
def debug_cheque_deposits(request):
   
    try:
        # Get all cheque deposits
        all_deposits = ChequeDeposit.objects.all().order_by('-deposit_date')
        pending_deposits = ChequeDeposit.objects.filter(status='pending').order_by('-deposit_date')
        
        # Print debug info
        print(f"DEBUG: Found {all_deposits.count()} total cheque deposits")
        print(f"DEBUG: Found {pending_deposits.count()} pending cheque deposits")
        
        for deposit in pending_deposits:
            print(f"DEBUG: Pending deposit ID: {deposit.id}, User: {deposit.user.username}, Amount: {deposit.amount}, Status: {deposit.status}")
        
        context = {
            'all_deposits': all_deposits,
            'pending_deposits': pending_deposits,
        }
        
        return render(request, 'debug_cheque_deposits.html', context)
        
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def status_tracking(request):
    cheque_number = request.GET.get('cheque_number')
    if cheque_number:
        try:
            cheque = ChequeDeposit.objects.get(cheque_number=cheque_number, user=request.user)
            status_updates = cheque.status_updates.all()
            context = {
                'cheque': cheque,
                'status_updates': status_updates
            }
            return render(request, 'status_tracking.html', context)
        except ChequeDeposit.DoesNotExist:
            context = {'error': 'Cheque not found'}
            return render(request, 'status_tracking.html', context)
    
    return render(request, 'status_tracking.html')

@login_required
def create_loan_notification(request):
   
    try:
        # Determine request type and extract data
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            data = request.POST
            
        loan_id = data.get('loan_id')
        status = data.get('status', '').upper()  # Normalize status to uppercase
        notes = data.get('notes', 'No additional notes provided')

        print(f"LOAN DEBUG: Processing loan {loan_id} with status {status}")  # Debug log
        
        # Process the loan with transaction handling
        with transaction.atomic():
            # Get loan with locking
            loan = LoanApplication.objects.select_for_update().get(id=loan_id)
            
            # Get the user model and user object
            User = get_user_model()
            user = User.objects.select_for_update().get(id=loan.user.id)
            
            print(f"LOAN DEBUG: Found loan: {loan.id}, amount: {loan.amount}, user: {user.username}")
            print(f"LOAN DEBUG: Current user balance before: {user.account_balance}, type: {type(user.account_balance)}")
            
            # Process based on status
            if status in ['APPROVE', 'APPROVED']:
                # Update loan status first
                loan.status = 'approved'
                loan.save()
                
                # Convert loan amount to Decimal if needed
                from decimal import Decimal
                if not isinstance(loan.amount, Decimal):
                    loan_amount = Decimal(str(loan.amount))
                else:
                    loan_amount = loan.amount
                
                print(f"LOAN DEBUG: Loan amount: {loan_amount}, type: {type(loan_amount)}")
                
                # APPROACH 1: Direct attribute update and save
                old_balance = user.account_balance
                user.account_balance = old_balance + loan_amount
                user.save()
                print(f"LOAN DEBUG: Updated balance (approach 1): {old_balance} -> {user.account_balance}")
                
                # APPROACH 2: Force a database update with F expression
                User.objects.filter(id=user.id).update(
                    account_balance=F('account_balance') + loan_amount
                )
                
                # Refresh user to get updated balance
                user.refresh_from_db()
                print(f"LOAN DEBUG: Updated balance (approach 2): {old_balance} -> {user.account_balance}")
                
                # APPROACH 3: Raw SQL update as a last resort
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        # Get the actual table name and column name
                        table_name = User._meta.db_table
                        cursor.execute(
                            f"UPDATE {table_name} SET account_balance = account_balance + %s WHERE id = %s",
                            [float(loan_amount), user.id]
                        )
                        print(f"LOAN DEBUG: Raw SQL update executed")
                except Exception as sql_error:
                    print(f"LOAN DEBUG: SQL error: {str(sql_error)}")
                
                # Refresh user again
                user.refresh_from_db()
                print(f"LOAN DEBUG: Final user balance: {user.account_balance}")
                
                # Create transaction record
                timestamp = int(time.time())
                reference_number = f"LOAN{timestamp}{get_random_string(8).upper()}"
                
                try:
                    # Create transaction with minimal fields
                    transaction_obj = Transaction(
                        sender=None,
                        recipient=user,
                        amount=loan_amount,
                        transaction_type='loan',
                        reference_number=reference_number,
                        description=f"Loan Disbursement - {loan.get_loan_type_display()}"
                    )
                    transaction_obj.save()
                    print(f"LOAN DEBUG: Created transaction: {transaction_obj.id}")
                except Exception as tx_error:
                    print(f"LOAN DEBUG: Transaction error: {str(tx_error)}")
                
                # Create notification message
                message = (
                    f"Congratulations! Your loan application for ${loan.amount} has been approved!\n"
                    f"The amount has been credited to your account.\n"
                    f"Loan Type: {loan.get_loan_type_display()}\n"
                    f"Purpose: {loan.purpose}"
                )
                
            elif status in ['REJECT', 'REJECTED']:
                # Update loan status
                loan.status = 'rejected'
                loan.save()
                
                # Create notification message
                message = (
                    f"Your loan application for ${loan.amount} has been rejected.\n"
                    f"Reason: {notes}"
                )
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                message=message,
                notification_type='loan'
            )
            
            print(f"LOAN DEBUG: Created notification: {notification.id}")
            
            # Return success response
            return JsonResponse({
                'success': True, 
                'message': f'Loan {loan.status} successfully',
                'loan_id': loan_id,
                'status': loan.status,
                'user_balance': float(user.account_balance)
            })
                
    except LoanApplication.DoesNotExist:
        print(f"LOAN DEBUG: Loan not found: {loan_id}")
        return JsonResponse({'success': False, 'error': 'Loan application not found'}, status=404)
        
    except Exception as e:
        print(f"LOAN DEBUG: Error in create_loan_notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@login_required
def get_user_accounts(request):
    try:
        # Get the current user
        user = request.user
        
        # Create account data based on the user's information
        savings_data = [{
            'id': 1,
            'accountNumber': user.account_number,
            'balance': float(user.account_balance),
            'type': 'Primary'
        }]
        
        # Get loan accounts if they exist
        loan_data = []
        try:
            # Get approved loans for the user
            loans = LoanApplication.objects.filter(
                user=user,
                status='approved'
            )
            
            for i, loan in enumerate(loans):
                loan_data.append({
                    'id': loan.id,
                    'loanId': f"L{loan.id}",
                    'outstanding': float(loan.amount),
                    'type': loan.get_loan_type_display()
                })
        except Exception as e:
            print(f"Error fetching loan data: {str(e)}")
            # Provide fallback loan data if there's an error
            loan_data = []
        
        # Return the data as JSON
        return JsonResponse({
            'savingsAccounts': savings_data,
            'loanAccounts': loan_data
        })
    except Exception as e:
        print(f"Error in get_user_accounts: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
def process_transaction(request):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            transaction_type = data.get('transaction_type')
            amount = data.get('amount')
            account_id = data.get('account_id')
            
            # Debug log to see what's coming in
            print(f"DEBUG: Received transaction data: {data}")
            print(f"DEBUG: Amount type: {type(amount)}, value: {amount}")
            
            # Convert amount to Decimal if it's a string
            if isinstance(amount, str):
                # Remove any non-numeric characters except decimal point
                amount_str = ''.join(c for c in amount if c.isdigit() or c == '.')
                if amount_str:
                    amount = Decimal(amount_str)
                else:
                    return JsonResponse({"status": "error", "message": "Invalid amount format"}, status=400)
            elif isinstance(amount, (int, float)):
                amount = Decimal(str(amount))
            elif amount is None:
                return JsonResponse({"status": "error", "message": "Amount is required"}, status=400)
            
            print(f"DEBUG: Converted amount: {amount}")
            
            # Find the user by account ID
            User = get_user_model()
            try:
                user = User.objects.get(id=account_id)
            except User.DoesNotExist:
                try:
                    # Try with account_number if id fails
                    user = User.objects.get(account_number=account_id)
                except User.DoesNotExist:
                    return JsonResponse({"status": "error", "message": f"User with account ID {account_id} not found"}, status=404)
            
            # Process based on transaction type
            if transaction_type == 'cheque_deposit' and data.get('status') == 'approved':
                # Credit the user's account
                user.account_balance += amount
                user.save()
                
                # Create a transaction record
                transaction = Transaction.objects.create(
                    sender=None,  # No sender for cheque deposits
                    recipient=user,
                    amount=amount,
                    transaction_type='deposit',
                    reference_number=f"CHQ{int(time.time())}{uuid.uuid4().hex[:8].upper()}",
                    description=f"Cheque Deposit - {data.get('cheque_number', 'Unknown')}"
                )
                
                # Create a notification for the user
                try:
                    from .models import Notification
                    Notification.objects.create(
                        user=user,
                        message=f"Your cheque deposit of ${amount} has been approved and credited to your account.",
                        notification_type='transaction'
                    )
                except Exception as e:
                    print(f"Error creating notification: {str(e)}")
                
                return JsonResponse({
                    "status": "success", 
                    "message": "Cheque deposit approved and account credited successfully.",
                    "transaction_id": str(transaction.id),
                    "user_name": user.get_full_name() or user.username,
                    "amount": float(amount),
                    "new_balance": float(user.account_balance)
                })
            
            # Handle other transaction types here
            
            return JsonResponse({"status": "success", "message": "Transaction processed successfully."})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
@csrf_exempt
def approve_cheque_deposit(request):
    
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            deposit_id = data.get('deposit_id')
            account_id = data.get('account_id')
            amount = data.get('amount')
            cheque_number = data.get('cheque_number')
            issuing_bank = data.get('issuing_bank')
            
            # Debug log
            print(f"DEBUG: Approving cheque deposit: {data}")
            
            # Validate required fields
            if deposit_id == 'NEW' or not account_id or not amount:
                return JsonResponse({
                    "status": "error", 
                    "message": "Invalid deposit data. Cannot approve a new or incomplete deposit."
                }, status=400)
            
            # Find the deposit
            try:
                deposit = ChequeDeposit.objects.get(id=deposit_id)
            except ChequeDeposit.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Cheque deposit with ID {deposit_id} not found"
                }, status=404)
            
            # Find the user account
            User = get_user_model()
            try:
                user = User.objects.get(id=account_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "message": f"User with ID {account_id} not found"
                }, status=404)
            
            # Update deposit status
            deposit.status = 'approved'
            
            # Try to set approved_by, but handle the case where the field might not exist yet
            try:
                deposit.approved_by = request.user
                deposit.approved_date = timezone.now()
            except Exception as e:
                print(f"Warning: Could not set approved_by or approved_date: {str(e)}")
                # Continue without setting these fields
            
            deposit.save()
            
            # Credit the user's account
            user.account_balance += Decimal(str(amount))
            user.save()
            
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                sender=None,  # System transaction
                recipient=user,
                amount=Decimal(str(amount)),
                transaction_type='CHEQUE_DEPOSIT',
                status='COMPLETED',
                reference_number=f"CHEQUE-{cheque_number}",
                description=f"Cheque deposit from {issuing_bank}, Cheque #{cheque_number}"
            )
            
            # Create notification for the user
            Notification.objects.create(
                user=user,
                message=f"Your cheque deposit of ${amount} has been approved and credited to your account.",
                notification_type='transaction'
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Cheque deposit approved successfully",
                "transaction_id": str(transaction_obj.id),
                "amount": float(amount),
                "new_balance": float(user.account_balance)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def credit_account(request):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            account_id = data.get('account_id')
            amount = data.get('amount')
            description = data.get('description', 'Account Credit')
            transaction_type = data.get('transaction_type', 'credit')
            
            print(f"DEBUG: Credit account data: {data}")
            
            # Convert amount to Decimal if it's a string
            if isinstance(amount, str):
                # Remove any non-numeric characters except decimal point
                amount_str = ''.join(c for c in amount if c.isdigit() or c == '.')
                if amount_str:
                    amount = Decimal(amount_str)
                else:
                    return JsonResponse({"status": "error", "message": "Invalid amount format"}, status=400)
            elif isinstance(amount, (int, float)):
                amount = Decimal(str(amount))
            elif amount is None:
                return JsonResponse({"status": "error", "message": "Amount is required"}, status=400)
            
            # Find the user by account ID
            User = get_user_model()
            try:
                user = User.objects.get(id=account_id)
            except User.DoesNotExist:
                try:
                    # Try with account_number if id fails
                    user = User.objects.get(account_number=account_id)
                except User.DoesNotExist:
                    return JsonResponse({"status": "error", "message": f"User with account ID {account_id} not found"}, status=404)
            
            # Credit the user's account
            with transaction.atomic():
                # Update user balance
                user.account_balance += amount
                user.save()
                
                # Create transaction record
                reference_number = f"CR{int(time.time())}{uuid.uuid4().hex[:8].upper()}"
                transaction_obj = Transaction.objects.create(
                    sender=None,
                    recipient=user,
                    amount=amount,
                    transaction_type=transaction_type,
                    reference_number=reference_number,
                    description=description
                )
                
                # Create notification
                try:
                    from .models import Notification
                    Notification.objects.create(
                        user=user,
                        message=f"Your account has been credited with ${amount}. {description}",
                        notification_type='transaction'
                    )
                except Exception as e:
                    print(f"Error creating notification: {str(e)}")
            
            return JsonResponse({
                "status": "success",
                "message": "Account credited successfully",
                "transaction_id": str(transaction_obj.id),
                "amount": float(amount),
                "new_balance": float(user.account_balance)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def get_account_holder(request):
    
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            account_id = data.get('account_id')
            account_number = data.get('account_number')
            
            print(f"DEBUG: Looking up account holder with ID: {account_id}, Number: {account_number}")
            
            if not account_id and not account_number:
                return JsonResponse({
                    "status": "error", 
                    "message": "Either account_id or account_number is required"
                }, status=400)
            
            # Find the user by account identifiers
            User = get_user_model()
            user = None
            
            # Try to find by account_id first
            if account_id:
                try:
                    user = User.objects.get(id=account_id)
                    print(f"DEBUG: Found user by ID: {user.username}")
                except User.DoesNotExist:
                    print(f"DEBUG: User with ID {account_id} not found")
                except Exception as e:
                    print(f"DEBUG: Error finding user by ID: {str(e)}")
            
            # If not found by ID, try account_number
            if user is None and account_number:
                try:
                    user = User.objects.get(account_number=account_number)
                    print(f"DEBUG: Found user by account number: {user.username}")
                except User.DoesNotExist:
                    print(f"DEBUG: User with account number {account_number} not found")
                except Exception as e:
                    print(f"DEBUG: Error finding user by account number: {str(e)}")
            
            # If user is still not found, return an error
            if user is None:
                return JsonResponse({
                    "status": "error", 
                    "message": "Account holder not found with the provided information"
                }, status=404)
            
            # Return the account holder information
            return JsonResponse({
                "status": "success",
                "account_holder": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.get_full_name(),
                    "email": user.email,
                    "account_number": user.account_number,
                    "is_active": user.is_active,
                    "account_balance": float(user.account_balance)
                }
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_pending_cheque_deposits(request):
    try:
        # Get pending cheque deposits
        pending_cheques = ChequeDeposit.objects.filter(status='pending').select_related('user').order_by('-deposit_date')
        
        # Debug print
        print(f"Found {pending_cheques.count()} pending cheque deposits")
        
        cheque_data = []
        for cheque in pending_cheques:
            cheque_data.append({
                'id': cheque.id,
                'user_name': cheque.user.get_full_name() or cheque.user.username,
                'user_id': cheque.user.id,
                'amount': str(cheque.amount),
                'cheque_number': cheque.cheque_number,
                'bank_name': cheque.bank_name,
                'deposit_date': cheque.deposit_date.strftime('%Y-%m-%d %H:%M'),
                'front_image': cheque.front_image.url if cheque.front_image else None,
                'back_image': cheque.back_image.url if cheque.back_image else None
            })
        
        return JsonResponse({'success': True, 'cheques': cheque_data})
    except Exception as e:
        print(f"Error in get_pending_cheque_deposits: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def get_cheque_deposit_details(request, deposit_id):
    
    # Ensure only staff/admin users can access
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized access"}, status=403)

    try:
        # Debugging logs to check received deposit_id
        print(f"🔍 Received deposit_id: {deposit_id}")

        # Special case for 'NEW' - return empty template for a new deposit
        if deposit_id == 'NEW':
            # Return a template for a new deposit
            empty_deposit = {
                "id": "NEW",
                "amount": 0.00,
                "cheque_number": "",
                "issuing_bank": "",
                "date_of_issue": "",
                "deposit_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": "",
                "user_name": "",
                "user_email": "",
                "status": "pending",
                "front_image": "",
                "back_image": ""
            }
            return JsonResponse({"success": True, "deposit": empty_deposit})

        # Validate if deposit_id is numeric for existing deposits
        if not str(deposit_id).isdigit():
            return JsonResponse({"error": "Invalid deposit ID format"}, status=400)

        # Retrieve cheque deposit
        deposit = get_object_or_404(ChequeDeposit, id=int(deposit_id))

        # Prepare response data
        formatted_deposit = {
            "id": deposit.id,
            "amount": float(deposit.amount),
            "cheque_number": deposit.cheque_number,
            "issuing_bank": deposit.bank_name or "Unknown",
            "date_of_issue": deposit.date_of_issue.strftime("%Y-%m-%d") if deposit.date_of_issue else "Unknown",
            "deposit_date": deposit.deposit_date.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": deposit.user.id,
            "user_name": deposit.user.get_full_name() or deposit.user.username,
            "user_email": deposit.user.email,
            "status": deposit.status,
        }

        # Add cheque images if available
        if deposit.front_image:
            formatted_deposit["front_image"] = request.build_absolute_uri(deposit.front_image.url)
        if deposit.back_image:
            formatted_deposit["back_image"] = request.build_absolute_uri(deposit.back_image.url)

        return JsonResponse({"success": True, "deposit": formatted_deposit})

    except Exception as e:
        print(f"❌ Error in get_cheque_deposit_details: {str(e)}")
        return JsonResponse({"success": False, "message": "An error occurred while retrieving cheque details"}, status=500)

@login_required
def get_user_cheques(request):
    user = request.user
    cheques = ChequeDeposit.objects.filter(user=user).order_by('-deposit_date')
    cheque_data = list(cheques.values())  # Convert QuerySet to list for JSON response
    return JsonResponse({'cheques': cheque_data})

@login_required
@csrf_exempt
def create_cheque_deposit(request):
    
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            account_id = data.get('account_id')
            amount = data.get('amount')
            cheque_number = data.get('cheque_number')
            issuing_bank = data.get('issuing_bank', '')
            date_of_issue = data.get('date_of_issue')
            
            # Debug log
            print(f"DEBUG: Creating new cheque deposit: {data}")
            
            # Validate required fields
            if not account_id or not amount or not cheque_number:
                return JsonResponse({
                    "status": "error", 
                    "message": "Account ID, amount, and cheque number are required"
                }, status=400)
            
            # Find the user account
            User = get_user_model()
            try:
                user = User.objects.get(id=account_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "message": f"User with ID {account_id} not found"
                }, status=404)
            
            # Convert amount to Decimal
            try:
                amount = Decimal(str(amount))
            except:
                return JsonResponse({
                    "status": "error", 
                    "message": "Invalid amount format"
                }, status=400)
            
            # Parse date if provided
            deposit_date = timezone.now()
            if date_of_issue:
                try:
                    date_of_issue = datetime.datetime.strptime(date_of_issue, "%Y-%m-%d").date()
                except:
                    date_of_issue = None
            
            # Create the cheque deposit
            deposit = ChequeDeposit.objects.create(
                user=user,
                amount=amount,
                cheque_number=cheque_number,
                issuing_bank=issuing_bank,
                date_of_issue=date_of_issue,
                deposit_date=deposit_date,
                status='pending'
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Cheque deposit created successfully",
                "deposit_id": deposit.id,
                "user_name": user.get_full_name() or user.username,
                "amount": float(amount)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def reject_cheque_deposit(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        deposit_id = data.get('deposit_id')
        
        # Validate required fields
        if not deposit_id:
            return JsonResponse({
                'status': 'error', 
                'message': 'Missing deposit ID'
            }, status=400)
        
        # Get the cheque deposit
        try:
            cheque = ChequeDeposit.objects.select_related('user').get(id=deposit_id)
        except ChequeDeposit.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': f'Cheque deposit with ID {deposit_id} not found'
            }, status=404)
        
        # Update the deposit status
        cheque.status = 'rejected'
        cheque.save()
        
        # Create a notification for the user
        Notification.objects.create(
            user=cheque.user,
            message=f'Your cheque deposit of ${cheque.amount} has been rejected.',
            notification_type='transaction'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Cheque deposit of ${cheque.amount} rejected successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
def manual_approve_cheque(request, cheque_id):
    
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        from .tasks import auto_approve_cheque
        
        # Get the cheque
        cheque = ChequeDeposit.objects.get(id=cheque_id)
        
        # Call the auto approve function directly
        result = auto_approve_cheque(cheque_id, cheque.user.id, cheque.amount)
        
        if result:
            return JsonResponse({
                'success': True,
                'message': f'Cheque {cheque_id} approved successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to approve cheque'
            })
    
    except ChequeDeposit.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Cheque with ID {cheque_id} not found'
        }, status=404)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
@login_required
def immediate_approve_cheque(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        cheque_id = request.POST.get('cheque_id')
        account_type = request.POST.get('account_type')
        account_id = request.POST.get('account_id')
        
        # Instead of immediate approval, schedule delayed approval
        from .utils import schedule_auto_approval, schedule_loan_payment_approval
        
        if account_type == 'loan' and account_id:
            # Schedule loan payment approval after 5 minutes
            schedule_loan_payment_approval(cheque_id, request.user.id, 
                                          ChequeDeposit.objects.get(id=cheque_id).amount, 
                                          account_id)
            
            return JsonResponse({
                'success': True,
                'message': 'Your loan payment has been scheduled and will be processed in 5 minutes.',
                'scheduled': True
            })
        else:
            # Schedule regular deposit approval after 5 minutes
            schedule_auto_approval(cheque_id, request.user.id, 
                                  ChequeDeposit.objects.get(id=cheque_id).amount)
            
            return JsonResponse({
                'success': True,
                'message': 'Your deposit has been scheduled and will be credited to your account in 5 minutes.',
                'scheduled': True
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def upload_cheque(request):
    """
    Handle cheque upload and deposit
    """
    if request.method == 'POST':
        try:
            # Extract form data
            amount = request.POST.get('amount')
            cheque_number = request.POST.get('cheque_number')
            bank_name = request.POST.get('bank_name')
            date_of_issue = request.POST.get('date_of_issue')
            account_type = request.POST.get('account_type')
            account_id = request.POST.get('account_id')
            
            # Handle file upload
            cheque_image = request.FILES.get('cheque_image')
            
            # Create a new ChequeDeposit record
            deposit = ChequeDeposit.objects.create(
                user=request.user,
                amount=Decimal(amount),
                cheque_number=cheque_number,
                bank_name=bank_name,
                date_of_issue=date_of_issue,
                front_image=cheque_image,
                status='pending',
                # Add branch_name and payee_name with default values
                branch_name='',
                payee_name=request.user.get_full_name() or request.user.username
            )
            
            # Schedule the auto-approval after 5 minutes
            if account_type == 'loan' and account_id:
                from .utils import schedule_loan_payment_approval
                schedule_loan_payment_approval(deposit.id, request.user.id, amount, account_id)
                print(f"Scheduled loan payment approval for cheque {deposit.id} in 5 minutes")
            else:
                from .utils import schedule_auto_approval
                schedule_auto_approval(deposit.id, request.user.id, amount)
                print(f"DEBUG: Scheduling auto approval for cheque {deposit.id}, user {request.user.id}, amount {amount} in 5 minutes")
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                message=f"Your cheque deposit of ${amount} has been received and will be processed in approximately 5 minutes.",
                notification_type='transaction'
            )
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Cheque deposit submitted successfully! It will be processed in approximately 5 minutes.',
                'deposit_id': deposit.id,
                'is_loan_payment': account_type == 'loan'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    # For GET requests, render the form
    return render(request, 'cheque_deposit.html')

@login_required
def get_user_balance(request):
    """
    API endpoint to get the current user's balance
    """
    try:
        # Get the current user
        user = request.user
        
        # Return the balance as JSON
        return JsonResponse({
            'success': True,
            'balance': float(user.account_balance)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# Keep this function as it is
def format_market_cap(market_cap):
    """Format market cap in billions or trillions"""
    if market_cap >= 1_000_000_000_000:
        return f"{market_cap/1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000_000:
        return f"{market_cap/1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:
        return f"{market_cap/1_000_000:.2f}M"
    else:
        return f"{market_cap:,.0f}"


def api_market_data(request):
    """API endpoint to get market data"""
    try:
        # Try to use yfinance for real market data
        try:
            import yfinance as yf
            from decimal import Decimal
            
            print("Fetching real market data with yfinance...")
            
            # Get major indices
            indices = {
                'sp500': '^GSPC',
                'nasdaq': '^IXIC',
                'nifty': '^NSEI'
            }
            
            data = {}
            
            for key, symbol in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # Get current price and previous close
                    current = info.get('regularMarketPrice', 0)
                    prev_close = info.get('previousClose', 0)
                    
                    if current and prev_close:
                        change_pct = ((current - prev_close) / prev_close) * 100
                    else:
                        change_pct = 0
                    
                    data[key] = {
                        'value': round(current, 2) if current else 0,
                        'change': round(change_pct, 2)
                    }
                except Exception as e:
                    print(f"Error fetching data for {symbol}: {str(e)}")
                    # Fallback to random data for this index
                    data[key] = {
                        'value': round(random.uniform(4000, 19000), 2),
                        'change': round(random.uniform(-2, 2), 2)
                    }
            
            return JsonResponse(data)
        
        except ImportError:
            print("yfinance not installed, using simulated data")
            # Fallback to random data
            raise Exception("Using fallback data")
            
    except Exception as e:
        print(f"Using simulated market data: {str(e)}")
        # Generate random market data for demo purposes
        data = {
            'sp500': {
                'value': round(random.uniform(4000, 4500), 2),
                'change': round(random.uniform(-2, 2), 2)
            },
            'nasdaq': {
                'value': round(random.uniform(13000, 14000), 2),
                'change': round(random.uniform(-2, 2), 2)
            },
            'nifty': {
                'value': round(random.uniform(18000, 19000), 2),
                'change': round(random.uniform(-2, 2), 2)
            }
        }
        return JsonResponse(data)

def api_stock_data(request, symbol):
    try:
        # Try to use yfinance for real stock data
        try:
            import yfinance as yf
            from decimal import Decimal
            
            print(f"Fetching real stock data for {symbol} with yfinance...")
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get basic info
            name = info.get('shortName', f"Unknown ({symbol})")
            price = info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', 0)
            volume = info.get('regularMarketVolume', 0)
            
            # Calculate change
            if price and prev_close:
                change = ((price - prev_close) / prev_close) * 100
            else:
                change = 0
            
            data = {
                'symbol': symbol.upper(),
                'name': name,
                'price': round(price, 2) if price else 0,
                'change': round(change, 2),
                'volume': volume,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'success': True
            }
            
            return JsonResponse(data)
            
        except ImportError:
            print("yfinance not installed, using simulated data")
            # Fallback to random data
            raise Exception("Using fallback data")
            
    except Exception as e:
        print(f"Using simulated stock data for {symbol}: {str(e)}")
        # Map of some common stock symbols to company names
        stock_names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com, Inc.',
            'META': 'Meta Platforms, Inc.',
            'TSLA': 'Tesla, Inc.',
            'NFLX': 'Netflix, Inc.',
            'RELIANCE.NS': 'Reliance Industries Ltd.',
            'TCS.NS': 'Tata Consultancy Services Ltd.',
            'INFY.NS': 'Infosys Ltd.'
        }
        
        name = stock_names.get(symbol.upper(), f"Unknown ({symbol})")
        price = round(random.uniform(50, 500), 2)
        change = round(random.uniform(-5, 5), 2)
        volume = random.randint(100000, 10000000)
        
        data = {
            'symbol': symbol.upper(),
            'name': name,
            'price': price,
            'change': change,
            'volume': volume,
            'success': True
        }
        
        return JsonResponse(data)



@login_required
def api_investment_real_time(request):
    """API endpoint to get real-time investment data using yfinance"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            investment_ids = data.get('investment_ids', [])
            
            # Get the user's investments
            if investment_ids:
                investments = Investment.objects.filter(id__in=investment_ids, user=request.user)
            else:
                investments = Investment.objects.filter(user=request.user)
            
            # Update investments with real-time data
            try:
                import yfinance as yf
                from decimal import Decimal
                
                print("Fetching real-time investment data with yfinance...")
                
                # Process each investment
                investment_data = []
                total_invested = Decimal('0')
                total_current_value = Decimal('0')
                
                for investment in investments:
                    total_invested += investment.amount
                    
                    if investment.symbol:
                        try:
                            # Get ticker data
                            ticker = yf.Ticker(investment.symbol)
                            
                            # Get current price
                            current_price = None
                            try:
                                current_price = ticker.info.get('regularMarketPrice')
                                if not current_price:
                                    # Try to get the current price from history
                                    hist = ticker.history(period="1d")
                                    if not hist.empty:
                                        current_price = hist['Close'].iloc[-1]
                            except Exception as e:
                                print(f"Error getting price data for {investment.symbol}: {str(e)}")
                            
                            if current_price:
                                # Update investment with current price
                                investment.current_price = Decimal(str(current_price))
                                investment.current_value = investment.shares * investment.current_price
                                investment.save()
                                
                                print(f"Updated {investment.symbol} price to {current_price}")
                        except Exception as e:
                            print(f"Error updating investment {investment.symbol}: {str(e)}")
                    
                    # Ensure current_value is set
                    if not investment.current_value:
                        investment.current_value = investment.amount
                        investment.save()
                    
                    # Calculate returns
                    returns = investment.current_value - investment.amount
                    return_percentage = (returns / investment.amount * 100) if investment.amount > 0 else Decimal('0')
                    
                    # Add to total
                    total_current_value += investment.current_value
                    
                    # Add to response data
                    investment_data.append({
                        'id': investment.id,
                        'symbol': investment.symbol,
                        'stock_name': investment.stock_name,
                        'shares': float(investment.shares),
                        'amount': float(investment.amount),
                        'current_price': float(investment.current_price),
                        'current_value': float(investment.current_value),
                        'returns': float(returns),
                        'return_percentage': float(return_percentage)
                    })
                
                # Calculate summary data
                total_returns = total_current_value - total_invested
                return_percentage = (total_returns / total_invested * 100) if total_invested > 0 else Decimal('0')
                
                return JsonResponse({
                    'success': True,
                    'investments': investment_data,
                    'summary': {
                        'total_invested': float(total_invested),
                        'total_current_value': float(total_current_value),
                        'total_returns': float(total_returns),
                        'return_percentage': float(return_percentage)
                    }
                })
                
            except ImportError:
                return JsonResponse({
                    'success': False,
                    'message': 'yfinance not installed on server'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })




@login_required
def get_account_balance(request, account_id):
    """API endpoint to get the latest balance for a specific account"""
    try:
        # Get the account for the current user with the specified ID
        account = Account.objects.get(id=account_id, user=request.user)
        
        # Log the account details for debugging
        print(f"Fetching balance for account ID {account_id}: {account.account_number} - ${account.balance}")
        
        return JsonResponse({
            'success': True,
            'balance': float(account.balance),
            'account_number': account.account_number,
            'account_type': account.account_type
        })
    except Account.DoesNotExist:
        print(f"Account with ID {account_id} not found for user {request.user.email}")
        return JsonResponse({
            'success': False,
            'message': 'Account not found'
        }, status=404)
    except Exception as e:
        print(f"Error fetching account balance: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def api_sell_investment(request):
    """API endpoint for selling investments"""
    if request.method == 'POST':
        try:
            investment_id = request.POST.get('investment_id')
            quantity = int(request.POST.get('quantity', 1))
            
            investment = Investment.objects.get(id=investment_id, user=request.user)
            
            # Validate quantity
            if quantity <= 0 or quantity > investment.shares:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid quantity. You have {investment.shares} shares available to sell.'
                }, status=400)
            
            # Calculate sell value
            sell_value = investment.current_value * (quantity / investment.shares)
            
            # Update account balance
            account = Account.objects.get(id=investment.account_id)
            account.balance += sell_value
            account.save()
            
            # If selling all shares, delete the investment
            if quantity >= investment.shares:
                investment.delete()
                message = f"Successfully sold all shares of {investment.stock_name} for ${sell_value:.2f}"
            else:
                # Otherwise, update the investment
                old_shares = investment.shares
                investment.shares -= quantity
                investment.amount = investment.amount * (investment.shares / old_shares)
                investment.current_value = investment.current_value * (investment.shares / old_shares)
                investment.save()
                message = f"Successfully sold {quantity} shares of {investment.stock_name} for ${sell_value:.2f}"
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        except Investment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Investment not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)



@login_required
def sell_investment(request, investment_id=None):
    if request.method == 'GET' and investment_id:
        try:
            investment = Investment.objects.get(id=investment_id, user=request.user)
            return render(request, 'sell_investment.html', {'investment': investment})
        except Investment.DoesNotExist:
            messages.error(request, "Investment not found.")
            return redirect('view_investments')

    elif request.method == 'POST':
        try:
            if not investment_id:
                content_type = request.content_type or ''
                if 'application/json' in content_type:
                    try:
                        data = json.loads(request.body)
                    except json.JSONDecodeError:
                        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
                    investment_id = data.get('investment_id')
                    quantity_str = data.get('quantity', '1')
                else:
                    investment_id = request.POST.get('investment_id')
                    quantity_str = request.POST.get('quantity', '1')
            else:
                quantity_str = request.POST.get('quantity', '1')
            
            quantity = int(float(quantity_str)) if quantity_str else 1
            
            with transaction.atomic():
                investment = Investment.objects.select_for_update().get(id=investment_id, user=request.user)
                
                if quantity <= 0 or quantity > investment.shares:
                    message = f'Invalid quantity. You have {investment.shares} shares available to sell.'
                    return JsonResponse({'success': False, 'message': message}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('sell_investment', investment_id=investment_id)
                
                sell_value = investment.current_value * (quantity / investment.shares)
                account = Account.objects.select_for_update().get(id=investment.account_id)
                old_balance = account.balance
                account.balance += Decimal(str(sell_value))
                account.save()
                
                Transaction.objects.create(
                    sender=None,
                    recipient=request.user,
                    amount=sell_value,
                    transaction_type='INVESTMENT_SALE',
                    status='COMPLETED',
                    reference_number=f'INV-SALE-{investment_id}',
                    description=f"Sale of {quantity} shares of {investment.stock_name}"
                )
                
                Notification.objects.create(
                    user=request.user,
                    message=f"Successfully sold {quantity} shares of {investment.stock_name} for ${sell_value:.2f}",
                    notification_type='INVESTMENT_SALE',
                    is_read=False
                )
                
                if quantity >= investment.shares:
                    investment.delete()
                    message = f"Successfully sold all shares of {investment.stock_name} for ${sell_value:.2f}"
                else:
                    old_shares = investment.shares
                    investment.shares -= quantity
                    investment.amount *= (investment.shares / old_shares)
                    investment.current_value *= (investment.shares / old_shares)
                    investment.save()
                    message = f"Successfully sold {quantity} shares of {investment.stock_name} for ${sell_value:.2f}"
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': message, 'new_balance': float(account.balance)})
                
                messages.success(request, message)
                return redirect('view_investments')
        
        except Investment.DoesNotExist:
            message = 'Investment not found'
            return JsonResponse({'success': False, 'message': message}, status=404) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('view_investments')
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('view_investments')

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('view_investments')


@login_required
def process_sell_investment(request, investment_id):
    """Process the sale of an investment"""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
        return redirect('view_investments')
    
    try:
        # Get the investment
        investment = Investment.objects.get(id=investment_id, user=request.user)
        
        # Get the quantity to sell
        quantity_str = request.POST.get('quantity', '0')
        try:
            quantity = int(float(quantity_str))
        except (ValueError, TypeError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)
            messages.error(request, 'Invalid quantity')
            return redirect('sell_investment', investment_id=investment_id)
        
        # Validate quantity
        if quantity <= 0 or quantity > investment.shares:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'Invalid quantity. You have {investment.shares} shares available to sell.'
                }, status=400)
            messages.error(request, f'Invalid quantity. You have {investment.shares} shares available to sell.')
            return redirect('sell_investment', investment_id=investment_id)
        
        # Process the sale with transaction atomic to ensure data consistency
        with transaction.atomic():
            # Calculate sell value based on current price
            sell_value = investment.current_value * (Decimal(quantity) / Decimal(investment.shares))
            
            # Update account balance
            account = Account.objects.select_for_update().get(user=request.user)
            old_balance = account.balance
            account.balance += sell_value
            account.save()
            
            # Also update the user's account_balance field for dashboard display
            request.user.account_balance += sell_value
            request.user.save(update_fields=['account_balance'])
            
            print(f"Updated account balance from ${old_balance} to ${account.balance}")
            
            # Create transaction record if requested
            if request.POST.get('record_transaction') == 'true':
                transaction_obj = Transaction.objects.create(
                    sender=None,  # System transaction
                    recipient=request.user,
                    amount=sell_value,
                    transaction_type='INVESTMENT_SALE',
                    status='COMPLETED',
                    reference_number=f'INV-SALE-{investment_id}',
                    description=f"Sale of {quantity} shares of {investment.stock_name}"
                )
                print(f"Created transaction record: {transaction_obj.id}")
            
            # Create notification if requested
            if request.POST.get('create_notification') == 'true':
                notification = Notification.objects.create(
                    user=request.user,
                    message=f"Successfully sold {quantity} shares of {investment.stock_name} for ${sell_value:.2f}",
                    notification_type='INVESTMENT_SALE',
                    is_read=False
                )
                print(f"Created notification: {notification.id}")
            
            # If selling all shares, delete the investment
            if quantity >= investment.shares:
                investment.delete()
                message = f"Successfully sold all shares of {investment.stock_name} for ${sell_value:.2f}"
            else:
                # Otherwise, update the investment
                old_shares = investment.shares
                investment.shares -= quantity
                investment.amount = investment.amount * (investment.shares / old_shares)
                investment.current_value = investment.current_value * (investment.shares / old_shares)
                investment.save()
                message = f"Successfully sold {quantity} shares of {investment.stock_name} for ${sell_value:.2f}"
        
        # Return response based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Refresh user object to get the latest balance
            request.user.refresh_from_db()
            return JsonResponse({
                'success': True,
                'message': message,
                'new_balance': float(request.user.account_balance),
                'account_number': request.user.account_number
            })
        
        messages.success(request, message)
        return redirect('view_investments')
        
    except Investment.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Investment not found'}, status=404)
        messages.error(request, 'Investment not found')
        return redirect('view_investments')
    except Exception as e:
        print(f"Error processing investment sale: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        messages.error(request, f'Error: {str(e)}')
        return redirect('view_investments')

@login_required
def sell_investment_page(request, investment_id):
    """Display the sell investment page - redirects to the main sell_investment function"""
    return sell_investment(request, investment_id)

@login_required
def create_investment(request):
    if request.method == 'POST':
        try:
            # Get form data
            symbol = request.POST.get('symbol')
            stock_name = request.POST.get('stock_name')
            shares_str = request.POST.get('shares')
            price_per_share_str = request.POST.get('price_per_share')
            account_number = request.POST.get('account_number')
            investment_type = request.POST.get('investment_type', 'stock')
            
            # Debug information
            print(f"Investment request: symbol={symbol}, stock={stock_name}, shares={shares_str}, price={price_per_share_str}, account={account_number}")
            
            # Validate input data
            if not all([symbol, stock_name, shares_str, price_per_share_str]):
                print("Missing required investment information")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': "Missing required investment information."
                    })
                messages.error(request, "Missing required investment information.")
                return redirect('investment_page')
            
            # Convert to Decimal safely
            try:
                shares = Decimal(shares_str)
                price_per_share = Decimal(price_per_share_str)
            except Exception as e:
                print(f"Invalid number format: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f"Invalid number format: {str(e)}"
                    })
                messages.error(request, f"Invalid number format: {str(e)}")
                return redirect('investment_page')
            
            # Find account - first try by account number
            account = None
            
            # Try to get account by account_number
            if account_number:
                try:
                    account = Account.objects.filter(account_number=account_number, user=request.user).first()
                    if account:
                        print(f"Found account by number: {account.account_number}")
                except Exception as e:
                    print(f"Error finding account by number: {str(e)}")
            
            # If still no account, get first available account
            if not account:
                try:
                    account = Account.objects.filter(user=request.user).first()
                    if account:
                        print(f"Using first available account: {account.account_number}")
                    else:
                        # Create a default account if none exists
                        import random
                        new_account_number = f"ACC{random.randint(10000, 99999)}"
                        account = Account.objects.create(
                            user=request.user,
                            account_number=new_account_number,
                            account_type='savings',
                            balance=10000.00  # Default balance for testing
                        )
                        print(f"Created new default account: {account.account_number}")
                except Exception as e:
                    print(f"Error finding/creating account: {str(e)}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': "Could not find or create an account."
                        })
                    messages.error(request, "Could not find or create an account.")
                    return redirect('investment_page')
            
            # Calculate total cost
            total_cost = shares * price_per_share
            print(f"Total investment cost: {total_cost}")
            
            # Check if account has sufficient balance
            if account.balance < total_cost:
                # Return error message about insufficient funds
                error_message = f"Insufficient funds. You need ${total_cost} but your balance is ${account.balance}."
                print(error_message)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message
                    })
                messages.error(request, error_message)
                return redirect('investment_page')
            
            # Create investment using transaction atomic to ensure data consistency
            with transaction.atomic():
                # Get account with select_for_update to prevent race conditions
                account = Account.objects.select_for_update().get(id=account.id)
                old_balance = account.balance
                
                # Create investment
                investment = Investment.objects.create(
                    user=request.user,
                    account=account,
                    symbol=symbol,
                    stock_name=stock_name,
                    shares=shares,
                    purchase_price=price_per_share,
                    current_price=price_per_share,
                    amount=total_cost,
                    current_value=total_cost,  # Initialize current value to purchase amount
                    investment_type=investment_type,
                    purchase_date=timezone.now()  # Add purchase date
                )
                
                # Deduct amount from account
                account.balance -= total_cost
                account.save()

                if hasattr(request.user, 'account_balance'):
                    request.user.account_balance = account.balance
                    request.user.save(update_fields=['account_balance'])
                
                
                print(f"Updated account {account.account_number} balance from ${old_balance} to ${account.balance}")
                
                # Create transaction record - removed 'account' parameter
                transaction_obj = Transaction.objects.create(
                    sender=request.user,
                    recipient=None,  # System transaction
                    amount=total_cost,
                    transaction_type='INVESTMENT_PURCHASE',
                    status='COMPLETED',
                    reference_number=f'INV-BUY-{investment.id}',
                    description=f"Investment in {shares} shares of {stock_name} ({symbol}) from account {account.account_number}"
                )
                
                print(f"Created transaction record: {transaction_obj.id}")
            
            # Create success notification
            notification = Notification.objects.create(
                user=request.user,
                message=f"Successfully invested in {shares} shares of {stock_name} for ${total_cost} from account {account.account_number}.",
                notification_type='INVESTMENT_PURCHASE'
            )
            
            print(f"Created notification: {notification.id}")
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Successfully invested in {shares} shares of {stock_name}.",
                    'investment_id': investment.id,
                    'new_balance': float(account.balance),  # Include the new balance in the response
                    'account_number': account.account_number  # Include account number for UI updates
                })
            
            messages.success(request, f"Successfully invested in {shares} shares of {stock_name}.")
            return redirect('investment_page')

        except Exception as e:
            print(f"Error processing investment: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                   'success': False,
                   'message': f"Error processing investment: {str(e)}"
                })
            messages.error(request, f"Error processing investment: {str(e)}")
            return redirect('investment_page')
    
    # Add a return statement for non-POST requests
    return redirect('investment_page')



@login_required
def export_loan_data(request):
    """
    Generate and download a CSV report of all loan applications
    """
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        # Import datetime correctly
        from datetime import datetime
        
        # Query all loan applications
        loan_applications = LoanApplication.objects.all().order_by('-applied_date')
        
        # Create the response with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="loan_applications_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        # Create CSV writer and write header
        writer = csv.writer(response)
        writer.writerow(['ID', 'Client Name', 'Loan Amount', 'Loan Type', 'Purpose', 
                         'Employment Status', 'Monthly Income', 'Status', 'Applied Date'])
        
        # Write loan application data
        for loan in loan_applications:
            writer.writerow([
                loan.id,
                f"{loan.user.first_name} {loan.user.last_name}" if hasattr(loan.user, 'first_name') else loan.user.username,
                loan.amount,
                loan.loan_type,
                loan.purpose,
                loan.employment_status,
                loan.monthly_income,
                loan.status,
                loan.applied_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    except Exception as e:
        # Log the error for debugging
        print(f"Error exporting loan data: {str(e)}")
        
        # Return error response
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_client_details(request):
    """View function to get client details for admin panel."""
    try:
        # Get filter parameter (all or active)
        filter_type = request.GET.get('filter', 'all')
        
        User = get_user_model()
        
        # Query clients based on filter
        if filter_type == 'active':
            clients = User.objects.filter(is_superuser=False, is_staff=False, is_active=True)
        else:  # 'all' or any other value
            clients = User.objects.filter(is_superuser=False, is_staff=False)
        
        # Prepare client data for response
        client_data = []
        for client in clients:
            client_data.append({
                'username': client.username,
                'name': f"{client.first_name} {client.last_name}",
                'email': client.email,
                'account_number': client.account_number,
                'account_balance': float(client.account_balance),
                'is_active': client.is_active,
                'date_joined': client.date_joined.strftime('%Y-%m-%d'),
                'last_login': client.last_login.strftime('%Y-%m-%d %H:%M') if client.last_login else 'Never'
            })
        
        return JsonResponse({'clients': client_data})
        
    except Exception as e:
        print(f"Error in get_client_details: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)



def settings(request):
    """
    View for user account settings page
    """
    # Get the user's account information
    user_account = None
    if hasattr(request.user, 'account'):
        user_account = request.user.account
    
    context = {
        'user_account': user_account,
    }
    
    return render(request, 'settings.html', context)

@login_required
def account_management(request):
    """
    View for account management page
    """
    # Get the user's account information
    user_account = None
    if hasattr(request.user, 'account'):
        user_account = request.user.account
    
    # Get transaction history - fetch the most recent 10 transactions
    transactions = []
    if user_account:
        from django.db.models import Q
        transactions = Transaction.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by('-timestamp')[:10]
    
    context = {
        'user_account': user_account,
        'transactions': transactions,
        'account_number': request.user.account_number,  # Add account number
        'account_balance': request.user.account_balance,  # Add account balance
    }
    
    return render(request, 'account_management.html', context)

@login_required
def update_personal_info(request):
    """
    View to update user's personal information
    """
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            
            # Update user information
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            # Return success response
            return JsonResponse({'success': True})
        except Exception as e:
            # Return error response
            return JsonResponse({'success': False, 'message': str(e)})
    
    # Return error for non-POST requests
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

    
@login_required
def change_password(request):
    """View function to handle password change."""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate passwords
        if not current_password or not new_password or not confirm_password:
            return JsonResponse({'success': False, 'message': 'All fields are required'})
            
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'New password and confirmation do not match'})
            
        # Check if current password is correct
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
            
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        return JsonResponse({'success': True, 'message': 'Password changed successfully'})
        
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def change_pin(request):
    """
    View to change user's PIN
    """
    if request.method == 'POST':
        try:
            current_pin = request.POST.get('current_pin')
            new_pin = request.POST.get('new_pin')
            confirm_pin = request.POST.get('confirm_pin')
            
            # Validate input
            if not all([current_pin, new_pin, confirm_pin]):
                return JsonResponse({'success': False, 'message': 'All fields are required'})
            
            if new_pin != confirm_pin:
                return JsonResponse({'success': False, 'message': 'New PINs do not match'})
            
            if len(new_pin) != 4 or not new_pin.isdigit():
                return JsonResponse({'success': False, 'message': 'PIN must be exactly 4 digits'})
            
            # Check if current PIN is correct
            if request.user.pin != current_pin:
                return JsonResponse({'success': False, 'message': 'Current PIN is incorrect'})
            
            # Update PIN directly on the User model
            request.user.pin = new_pin
            request.user.save()
            
            return JsonResponse({'success': True, 'message': 'PIN changed successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def update_notification_preferences(request):
    """
    View to update user's notification preferences
    """
    if request.method == 'POST':
        try:
            # Get form data
            email_notifications = request.POST.get('email_notifications') == 'true'
            sms_notifications = request.POST.get('sms_notifications') == 'true'
            marketing_emails = request.POST.get('marketing_emails') == 'true'
            
  
            user_preferences, created = UserPreference.objects.get_or_create(user=request.user)
            user_preferences.email_notifications = email_notifications
            user_preferences.sms_notifications = sms_notifications
            user_preferences.marketing_emails = marketing_emails
            user_preferences.save()
            
            # Return success response
            return JsonResponse({'success': True})
        except Exception as e:
            # Return error response
            return JsonResponse({'success': False, 'message': str(e)})
    
    # Return error for non-POST requests
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def download_statement(request):
    """View for downloading account statements"""
    # Get parameters from request
    period = request.GET.get('period', 'last_month')
    format_type = request.GET.get('format', 'pdf')
    from_date = request.GET.get('from_date', None)
    to_date = request.GET.get('to_date', None)
    
    # Calculate date range based on period
    today = timezone.now().date()
    if period == 'last_month':
        start_date = today.replace(day=1) - datetime.timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = today
    elif period == 'last_3_months':
        start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        start_date = (start_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        start_date = (start_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        end_date = today
    elif period == 'last_6_months':
        start_date = today - datetime.timedelta(days=180)
        end_date = today
    elif period == 'custom' and from_date and to_date:
        try:
            start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return HttpResponse("Invalid date format", status=400)
    else:
        start_date = today - datetime.timedelta(days=30)
        end_date = today
    
    # Get transactions for the date range
    transactions = Transaction.objects.filter(
        models.Q(sender=request.user) | models.Q(recipient=request.user),
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).order_by('-timestamp')
    
    # Generate appropriate response based on format
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="account_statement_{start_date}_to_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Balance'])
        
        for transaction in transactions:
            is_credit = transaction.recipient == request.user
            writer.writerow([
                transaction.timestamp.strftime('%Y-%m-%d %H:%M'),
                transaction.description or ('Received payment' if is_credit else 'Payment sent'),
                transaction.amount,
                'Credit' if is_credit else 'Debit',
                ''  # Balance would need to be calculated
            ])
        
        return response
    
    elif format_type == 'excel':
        # For simplicity, we'll return CSV for Excel too
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="account_statement_{start_date}_to_{end_date}.xls"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Balance'])
        
        for transaction in transactions:
            is_credit = transaction.recipient == request.user
            writer.writerow([
                transaction.timestamp.strftime('%Y-%m-%d %H:%M'),
                transaction.description or ('Received payment' if is_credit else 'Payment sent'),
                transaction.amount,
                'Credit' if is_credit else 'Debit',
                ''  # Balance would need to be calculated
            ])
        
        return response
    
    else:  
       
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="account_statement_{start_date}_to_{end_date}.pdf"'
        response.write(b'%PDF-1.4\n%Sample PDF Statement')
        return response



def services(request):
  return render(request, 'services.html')

def about_us(request):
   return render(request, 'about_us.html')


def contact(request):
    if request.method == 'POST':
        try:
            # Parse JSON body
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            message = data.get('message')

            # You can process/save/send email here if needed

            # Return JSON response
            return JsonResponse({'success': True, 'message': 'Your message has been sent. We will get back to you soon!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # For GET request, just render the form page
    return render(request, 'contact.html')  

def get_started(request):
  return render(request, 'get_started.html')

def learn_more(request):
   return render(request, 'learn_more.html')

def security_features(request):
   return render(request, 'security_features.html')

def download_app(request):
 
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_ios = 'iphone' in user_agent or 'ipad' in user_agent
    is_android = 'android' in user_agent
    
    context = {
        'is_ios': is_ios,
        'is_android': is_android,
        'is_mobile': is_ios or is_android,
    }
    
    return render(request, 'download_app.html', context)

@login_required
def quick_transfer_view(request):
    # Get today's date
    today = timezone.now().date()
    
    # Set daily limit to $5000 for all users
    daily_limit_total = Decimal('5000.00')
    
    # Calculate daily used amount from today's transactions for THIS USER ONLY
    daily_used_amount = Transaction.objects.filter(
        sender=request.user,
        transaction_type='TRANSFER',
        timestamp__date=today,
        status='COMPLETED'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate daily limit remaining - ensure it's never negative
    daily_limit_remaining = max(daily_limit_total - daily_used_amount, Decimal('0.00'))
    
    # Calculate percentage used
    daily_used_percentage = min((daily_used_amount / daily_limit_total) * 100, 100) if daily_limit_total > 0 else 0
    
    # Get recent transfers
    recent_transfers = Transaction.objects.filter(
        sender=request.user,
        transaction_type='TRANSFER',
        status='COMPLETED'
    ).order_by('-timestamp')[:5]
    
    context = {
        'recent_transfers': recent_transfers,
        'daily_limit_total': daily_limit_total,
        'daily_used_amount': daily_used_amount,
        'daily_limit_remaining': daily_limit_remaining,
        'daily_used_percentage': daily_used_percentage,
    }
    
    return render(request, 'quick_transfer.html', context)

@login_required
def api_user_accounts(request):
    """API endpoint to get user accounts with fresh data"""
    try:
        # Force a fresh query to get the most up-to-date account information
        user_accounts = Account.objects.filter(user=request.user).select_for_update(skip_locked=True)
        
        # Format account data for response
        accounts_data = []
        for account in user_accounts:
            accounts_data.append({
                'id': account.id,
                'account_number': account.account_number,
                'account_type': account.account_type,
                'balance': float(account.balance)
            })
        
        # Debug output
        print(f"API User Accounts: Found {len(accounts_data)} accounts for user {request.user.username}")
        for acc in accounts_data:
            print(f"  - Account: {acc['account_number']}, Balance: ${acc['balance']}")
        
        # Also include the user's account_balance field for comparison
        user_account_balance = float(request.user.account_balance) if hasattr(request.user, 'account_balance') else None
        
        return JsonResponse({
            'success': True,
            'accounts': accounts_data,
            'user_account_balance': user_account_balance
        })
    except Exception as e:
        print(f"Error in api_user_accounts: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def investment_page(request):
    # Get user's accounts
    user_accounts = Account.objects.filter(user=request.user)
    
    # Sync account balance with user.account_balance if needed
    if hasattr(request.user, 'account_balance') and user_accounts.exists():
        account = user_accounts.first()
        if account.balance != request.user.account_balance:
            print(f"Syncing account balance: Account model: ${account.balance}, User model: ${request.user.account_balance}")
            # Update the account balance to match the user.account_balance
            account.balance = request.user.account_balance
            account.save()
    
    # Refresh the accounts query to get updated data
    user_accounts = Account.objects.filter(user=request.user)
    
    # Debug output
    print(f"Found {user_accounts.count()} accounts for user {request.user.username}")
    for account in user_accounts:
        print(f"Account: {account.account_number}, Balance: {account.balance}")
    
    # Get user's investments
    investments = Investment.objects.filter(user=request.user)
    
    # Calculate total investment value (from investment_view)
    total_investment_value = sum(investment.current_value or 0 for investment in investments)
    
    context = {
        'user_accounts': user_accounts,
        'investments': investments,
        'total_investment_value': total_investment_value,
    }
    
    return render(request, 'investment.html', context)

@login_required
def stock_data_api(request):
    """API endpoint to fetch stock data from Yahoo Finance"""
    symbol = request.GET.get('symbol', '')
    if not symbol:
        return JsonResponse({'success': False, 'message': 'Symbol is required'})
    
    try:
        # Use yfinance to get stock data
        stock = tf.Ticker(symbol)
        stock_info = stock.info
        
        # Get current price data
        history = stock.history(period="1d")
        current_price = round(history['Close'].iloc[-1], 2) if not history.empty else 0
        
        # Calculate change percentage
        previous_close = stock_info.get('previousClose', 0)
        change_percent = round(((current_price - previous_close) / previous_close * 100), 2) if previous_close else 0
        
        # Format response data
        data = {
            'symbol': symbol.upper(),
            'name': stock_info.get('shortName', f"{symbol.upper()} Stock"),
            'price': current_price,
            'change': change_percent,
            'volume': stock_info.get('volume', 0),
            'market_cap': stock_info.get('marketCap', 0),
            'pe_ratio': stock_info.get('trailingPE', 0),
            'dividend_yield': stock_info.get('dividendYield', 0) * 100 if stock_info.get('dividendYield') else 0,
        }
        
        return JsonResponse({'success': True, 'data': data})
    
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Error fetching stock data: {str(e)}'})


@login_required
def update_limits(request):
    """Update user account limits"""
    if request.method == 'POST':
        try:
            # Get the new limits from the form
            daily_transfer_limit = Decimal(request.POST.get('daily_transfer_limit', '5000.00'))
            atm_limit = Decimal(request.POST.get('atm_limit', '1000.00'))
            online_limit = Decimal(request.POST.get('online_limit', '2000.00'))
            
            # Update the user's limits
            request.user.daily_transfer_limit = daily_transfer_limit
            
            
            # Save the changes
            request.user.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_market_data(request):
    """API endpoint to fetch market data from Yahoo Finance."""
    try:
        # Fetch S&P 500 data
        sp500 = tf.Ticker("^GSPC")
        sp500_info = sp500.info
        sp500_history = sp500.history(period="1d")
        sp500_current = sp500_history['Close'].iloc[-1]
        sp500_prev = sp500_history['Open'].iloc[0]
        sp500_change = ((sp500_current - sp500_prev) / sp500_prev) * 100
        
        # Fetch NASDAQ data
        nasdaq = tf.Ticker("^IXIC")
        nasdaq_info = nasdaq.info
        nasdaq_history = nasdaq.history(period="1d")
        nasdaq_current = nasdaq_history['Close'].iloc[-1]
        nasdaq_prev = nasdaq_history['Open'].iloc[0]
        nasdaq_change = ((nasdaq_current - nasdaq_prev) / nasdaq_prev) * 100
        
        # Fetch NIFTY 50 data
        nifty = tf.Ticker("^NSEI")
        nifty_info = nifty.info
        nifty_history = nifty.history(period="1d")
        nifty_current = nifty_history['Close'].iloc[-1]
        nifty_prev = nifty_history['Open'].iloc[0]
        nifty_change = ((nifty_current - nifty_prev) / nifty_prev) * 100
        
        # Format the data
        return JsonResponse({
            'success': True,
            'sp500': {
                'value': f"{sp500_current:,.2f}",
                'change': f"{'+' if sp500_change >= 0 else ''}{sp500_change:.2f}%"
            },
            'nasdaq': {
                'value': f"{nasdaq_current:,.2f}",
                'change': f"{'+' if nasdaq_change >= 0 else ''}{nasdaq_change:.2f}%"
            },
            'nifty': {
                'value': f"{nifty_current:,.2f}",
                'change': f"{'+' if nifty_change >= 0 else ''}{nifty_change:.2f}%"
            }
        })
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error fetching market data'
        })

@login_required
def create_account_api(request):
    if request.method == 'POST':
        account_type = request.POST.get('account_type')
        initial_deposit = request.POST.get('initial_deposit')
        
        try:
            # Validate input
            if not account_type or not initial_deposit:
                return JsonResponse({'success': False, 'message': 'Missing required fields'})
            
            initial_deposit = float(initial_deposit)
            if initial_deposit < 100:  # Minimum deposit requirement
                return JsonResponse({'success': False, 'message': 'Minimum initial deposit is $100'})
            
            # Generate account number
            import random
            account_number = f"ACC{random.randint(10000, 99999)}"
            
            # Create account
            account = Account.objects.create(
                user=request.user,
                account_number=account_number,
                account_type=account_type,
                balance=initial_deposit
            )
            
            # Create initial deposit transaction - modify this to match your Transaction model
           
            Transaction.objects.create(
                sender=None,  # For initial deposit, there's no sender
                recipient=request.user,
                amount=initial_deposit,
                transaction_type='DEPOSIT',
                status='COMPLETED',
                description=f'Initial deposit to {account_type} account'
            )
            
            # Return success response with account details
            return JsonResponse({
                'success': True, 
                'message': 'Account created successfully',
                'account': {
                    'id': account.id,
                    'account_number': account.account_number,
                    'account_type': account.account_type,
                    'balance': float(account.balance),
                    'date_created': account.date_created.strftime('%Y-%m-%d')
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def view_investments(request):
    
    # Get user's investments
    investments = Investment.objects.filter(user=request.user)
    
    # Calculate totals
    total_invested = sum(investment.amount for investment in investments)
    
    # Update current prices for each investment
    for investment in investments:
        try:
            print(f"Updating price for {investment.symbol}...")
            # Get current market price using yfinance
            ticker = investment.symbol
            stock_data = tf.Ticker(ticker)
            current_price = stock_data.history(period="1d")['Close'].iloc[-1]
            
            print(f"Got current price for {investment.symbol}: ${current_price}")
            
            # Calculate current value based on shares and current price
            old_value = investment.current_value
            investment.current_value = float(investment.shares) * current_price
            print(f"Updated value for {investment.symbol} from ${old_value} to ${investment.current_value}")
            
            # Save the updated investment
            investment.save()
        except Exception as e:
            print(f"Error updating price for {investment.symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Recalculate totals after price updates - IMPORTANT: Fetch fresh data from database
    updated_investments = Investment.objects.filter(user=request.user)
    total_current_value = sum(investment.current_value for investment in updated_investments)
    total_returns = total_current_value - total_invested
    return_percentage = (total_returns / total_invested * 100) if total_invested > 0 else 0
    
    # Print debug information
    print(f"Total invested: ${total_invested}")
    print(f"Total current value: ${total_current_value}")
    print(f"Total returns: ${total_returns}")
    print(f"Return percentage: {return_percentage}%")
    
    context = {
        'investments': updated_investments,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_returns': total_returns,
        'return_percentage': return_percentage,
    }
    
    # Make sure this template name matches exactly with your template file
    return render(request, 'investments.html', context)
@login_required
def api_investments(request):
    """API endpoint to get investment data"""
    try:
        # Get user's investments
        investments = Investment.objects.filter(user=request.user)
        
        # Calculate initial total invested
        total_invested = sum(float(investment.amount) for investment in investments)
        
        # Update current prices and values for each investment
        investments_data = []
        total_current_value = 0
        
        for investment in investments:
            try:
                # Get current market price using yfinance
                ticker = investment.symbol
                stock_data = tf.Ticker(ticker)
                current_price = stock_data.history(period="1d")['Close'].iloc[-1]
                
                # Apply currency conversion for Indian stocks (if needed)
                
                is_indian_stock = ticker.endswith('.NS')
                
                # Calculate current value based on shares and current price
                shares = float(investment.shares)
                
                # For Indian stocks, we need to handle the currency conversion properly
                if is_indian_stock:
                    # For Indian stocks, the price is in INR but we display in USD
                    # Using a more accurate conversion rate (adjust as needed)
                    inr_to_usd = 1/83.5  
                    current_value = shares * current_price * inr_to_usd
                    print(f"Indian stock {ticker}: Price in INR: {current_price}, Converted value: ${current_value}")
                else:
                    current_value = shares * current_price
                    print(f"US stock {ticker}: Price: ${current_price}, Value: ${current_value}")
                
                # Update the investment object
                investment.current_value = current_value
                investment.save()
                
                # Add to total current value
                total_current_value += current_value
                
                # Calculate returns
                returns = current_value - float(investment.amount)
                return_percentage = (returns / float(investment.amount) * 100) if float(investment.amount) > 0 else 0
                
                # Add investment data to response
                investments_data.append({
                    'id': investment.id,
                    'symbol': investment.symbol,
                    'stock_name': investment.stock_name,
                    'shares': shares,
                    'amount': float(investment.amount),
                    'current_value': current_value,
                    'returns': returns,
                    'return_percentage': return_percentage,
                    'is_indian_stock': is_indian_stock
                })
            except Exception as e:
                print(f"Error updating price for {investment.symbol}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Calculate total returns and percentage
        total_returns = total_current_value - total_invested
        return_percentage = (total_returns / total_invested * 100) if total_invested > 0 else 0
        
        print(f"API - Total invested: ${total_invested}")
        print(f"API - Total current value: ${total_current_value}")
        print(f"API - Total returns: ${total_returns}")
        print(f"API - Return percentage: {return_percentage}%")
        
        return JsonResponse({
            'success': True,
            'investments': investments_data,
            'total_invested': total_invested,
            'total_current_value': total_current_value,
            'total_returns': total_returns,
            'return_percentage': return_percentage
        })
    except Exception as e:
        print(f"Error in api_investments: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# Add this to your existing view functions
def help_view(request):
    return render(request, 'help.html')


