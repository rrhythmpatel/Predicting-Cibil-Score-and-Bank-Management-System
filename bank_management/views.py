from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils import timezone
from core.models import Transaction
from django.http import JsonResponse

def is_admin_user(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin_user, login_url='login')
def admin_panel(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return redirect('login')
    
    try:
        User = get_user_model()
        
        # Calculate user statistics
        total_clients = User.objects.filter(is_staff=False, is_superuser=False).count()
        active_accounts = User.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()
        pending_accounts = User.objects.filter(is_active=False, is_staff=False, is_superuser=False).count()
        
        # Get 24-hour transaction data
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        transactions_24h = Transaction.objects.filter(timestamp__gte=last_24h).aggregate(
            total_amount=Sum('amount'),
            count=Count('id')
        )
        
        # Get recent client activity
        recent_users = User.objects.filter(
            is_staff=False, 
            is_superuser=False
        ).order_by('-last_login')[:10]
        
        context = {
            'total_clients': total_clients,
            'active_accounts': active_accounts,
            'pending_accounts': pending_accounts,
            'transactions_24h': transactions_24h['total_amount'] or 0,
            'transactions_count': transactions_24h['count'] or 0,
            'recent_users': recent_users,
            'is_admin': True
        }
        
        print("Debug - Admin Panel Data:", context)  # Debug print
        
        return render(request, 'admin_panel.html', context)
        
    except Exception as e:
        print(f"Error in admin_panel: {str(e)}")
        context = {'error': str(e), 'is_admin': True}
        return render(request, 'admin_panel.html', context)

@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_panel')
    return render(request, 'dashboard.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_panel')  # Use URL name instead of hardcoded path
            return redirect('dashboard')
    return render(request, 'loginpage.html')
@login_required
def admin_panel(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('dashboard')
    context = {
        'user': request.user,
        'is_admin': True
    }
    return render(request, 'admin_panel.html', context)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_panel')  # Use URL name
            return redirect('dashboard')
    return render(request, 'loginpage.html')
def user_logout(request):
    logout(request)
    return redirect('homepage')

def fund_transfer(request):
    return render(request, 'fund_transfer.html')


from django.http import JsonResponse

@login_required
def get_cibil_data(request, client_id):
    """
    Fetch CIBIL data for a specific client
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get the client
        client = User.objects.get(id=client_id)
        
        # Log the client details for debugging
        print(f"Fetching CIBIL data for client: {client.username} (ID: {client.id})")
        
        # Generate a deterministic CIBIL score based on the client's username
        import hashlib
        
        # Create a hash from the username
        hash_object = hashlib.md5(client.username.encode())
        hash_hex = hash_object.hexdigest()
        
        # Convert the first 8 characters of the hash to an integer and scale to 300-900 range
        score_base = int(hash_hex[:8], 16)
        cibil_score = 300 + (score_base % 600)
        
        # Determine eligibility based on score
        eligibility = 'Not Eligible'
        interest_rate = '16.5%+'
        
        if cibil_score >= 750:
            eligibility = 'Eligible'
            interest_rate = '10.5%'
        elif cibil_score >= 700:
            eligibility = 'Conditionally Eligible'
            interest_rate = '12.5%'
        elif cibil_score >= 650:
            eligibility = 'Conditionally Eligible'
            interest_rate = '14.5%'
        
        # Return the CIBIL data
        return JsonResponse({
            'score': cibil_score,
            'eligibility': eligibility,
            'interest_rate': interest_rate
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': f'Client with ID {client_id} not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_loan_details(request, loan_id):
    """
    Get details for a specific loan application
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get the loan application
        loan = LoanApplication.objects.get(id=loan_id)
        
        # Return the loan details including the user_id
        return JsonResponse({
            'id': loan.id,
            'client_name': f"{loan.user.first_name} {loan.user.last_name}",
            'client_id': loan.user.id,  # Include the user ID explicitly
            'user_id': loan.user.id,    # Include as user_id as well for redundancy
            'amount': loan.amount,
            'loan_type': loan.loan_type,
            'purpose': loan.purpose,
            'monthly_income': loan.monthly_income,
            'employment_status': loan.employment_status,
            'status': loan.status,
            'applied_date': loan.applied_date.strftime('%Y-%m-%d %H:%M')
        })
    except LoanApplication.DoesNotExist:
        return JsonResponse({'error': 'Loan application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_account_balance(request, account_id):
    """API endpoint to get the latest balance for a specific account"""
    try:
        account = Account.objects.get(id=account_id, user=request.user)
        return JsonResponse({
            'success': True,
            'balance': float(account.balance)
        })
    except Account.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Account not found'
        }, status=404)


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils import timezone
from core.models import Transaction
from django.http import JsonResponse, HttpResponse
import csv
from datetime import datetime, timedelta

# ... existing code ...

@login_required
@user_passes_test(is_admin_user)
def download_transaction_report(request):
    """
    Generate and download a CSV report of transactions based on the specified time period
    """
    try:
        # Get the number of days from the request (default to 7 days)
        days = int(request.GET.get('days', 7))
        
        # Calculate the date range
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Query transactions within the date range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('-timestamp')
        
        # Create the response with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transaction_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        # Create CSV writer and write header
        writer = csv.writer(response)
        writer.writerow(['Transaction ID', 'Date', 'User', 'Type', 'Amount', 'Status'])
        
        # Write transaction data
        for transaction in transactions:
            writer.writerow([
                transaction.id,
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                transaction.user.username if hasattr(transaction, 'user') and transaction.user else 'N/A',
                getattr(transaction, 'transaction_type', 'N/A'),
                transaction.amount,
                getattr(transaction, 'status', 'Completed')
            ])
        
        return response
    except Exception as e:
        # Log the error for debugging
        print(f"Error generating transaction report: {str(e)}")
        
        # Return error response
        return JsonResponse({'error': str(e)}, status=500)


        
