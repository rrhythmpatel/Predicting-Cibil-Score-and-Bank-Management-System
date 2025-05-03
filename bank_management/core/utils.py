import threading
import time
from decimal import Decimal

def schedule_auto_approval(cheque_id, user_id, amount):
    """
    Schedule automatic approval of a cheque deposit after a delay (30 second)
    """
    def delayed_approval():
        # Sleep for 5 minutes (300 seconds)
        time.sleep(30)  # 300 seconds = 5 minutes
        
        # Import here to avoid circular imports
        from .models import ChequeDeposit, Transaction, Notification
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from django.utils.crypto import get_random_string
        from django.utils import timezone
        
        try:
            # Use transaction atomic to ensure database consistency
            with transaction.atomic():
                # Get the user model
                User = get_user_model()
                
                # Get the cheque deposit with select_for_update to lock the row
                cheque = ChequeDeposit.objects.select_for_update().get(id=cheque_id)
                
                # Check if the cheque is still pending
                if cheque.status != 'pending':
                    print(f"Cheque {cheque_id} is no longer pending, status: {cheque.status}")
                    return
                
                # Get the user
                user = User.objects.select_for_update().get(id=user_id)
                
                # Process the deposit
                amount_decimal = Decimal(str(amount))
                
                # Update user balance
                old_balance = user.account_balance
                user.account_balance += amount_decimal
                user.save()
                
                print(f"User balance updated after 30 second: {old_balance} -> {user.account_balance}")
                
                # Update cheque status
                cheque.status = 'approved'
                cheque.approved_date = timezone.now()
                cheque.save()
                
                # Generate a unique reference number with timestamp to avoid collisions
                reference_number = f"CHEQUE-{cheque.cheque_number}-{int(timezone.now().timestamp())}"
                
                # Create transaction record
                Transaction.objects.create(
                    sender=None,  # System transaction
                    recipient=user,
                    amount=amount_decimal,
                    transaction_type='CHEQUE_DEPOSIT',
                    status='COMPLETED',
                    reference_number=reference_number,
                    description=f"Cheque deposit from {cheque.bank_name}, Cheque #{cheque.cheque_number}"
                )
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    message=f"Your cheque deposit of ${amount_decimal} has been approved and credited to your account after verification.",
                    notification_type='transaction'
                )
                
                print(f"Cheque deposit processed successfully for cheque {cheque_id} after 5-minute verification")
                
        except Exception as e:
            print(f"Error in delayed_approval: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Start the thread
    thread = threading.Thread(target=delayed_approval)
    thread.daemon = True
    thread.start()
    
    print(f"Scheduled automatic approval for cheque {cheque_id} in 30 second")
    
    return True

def schedule_loan_payment_approval(cheque_id, user_id, amount, loan_id):
    """
    Schedule automatic approval of a cheque deposit for loan payment after a delay (30 second)
    """
    def delayed_loan_payment():
        # Sleep for 5 minutes (300 seconds)
        time.sleep(30)  # 300 seconds = 5 minutes
        
        # Import here to avoid circular imports
        from .models import ChequeDeposit, Transaction, Notification, LoanApplication
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from django.utils.crypto import get_random_string
        from django.utils import timezone
        
        try:
            # Use transaction atomic to ensure database consistency
            with transaction.atomic():
                # Get the user model
                User = get_user_model()
                
                # Get the cheque deposit with select_for_update to lock the row
                cheque = ChequeDeposit.objects.select_for_update().get(id=cheque_id)
                
                # Check if the cheque is still pending
                if cheque.status != 'pending':
                    print(f"Cheque {cheque_id} is no longer pending, status: {cheque.status}")
                    return
                
                # Get the user
                user = User.objects.select_for_update().get(id=user_id)
                
                # Get the loan
                loan = LoanApplication.objects.select_for_update().get(id=loan_id, user=user)
                
                # Process the loan payment
                amount_decimal = Decimal(str(amount))
                
                # Update loan balance
                old_balance = loan.amount
                loan.amount = max(Decimal('0'), loan.amount - amount_decimal)
                
                # If loan is fully paid, update status
                if loan.amount <= Decimal('0'):
                    loan.status = 'paid'
                    
                # Save the loan with updated amount
                loan.save()
                
                # Update user's account balance (deduct the payment amount)
                old_user_balance = user.account_balance
                user.account_balance -= amount_decimal
                user.save()
                
                print(f"User balance updated after 30 second: {old_user_balance} -> {user.account_balance}")
                print(f"Loan {loan_id} balance updated after 30 second: {old_balance} -> {loan.amount}")
                
                # Update cheque status
                cheque.status = 'approved'
                cheque.approved_date = timezone.now()
                cheque.save()
                
                # Generate a unique reference number with timestamp to avoid collisions
                reference_number = f"LOAN-{get_random_string(8).upper()}-{int(timezone.now().timestamp())}"
                
                # Create transaction record
                Transaction.objects.create(
                    sender=user,
                    recipient=None,  # No recipient for loan payments
                    amount=amount_decimal,
                    transaction_type='LOAN_PAYMENT',
                    status='COMPLETED',
                    reference_number=reference_number,
                    description=f"Loan Payment - Cheque {cheque.cheque_number}"
                )
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    message=f"Your cheque deposit of ${amount_decimal} has been approved and applied to your loan after verification. New outstanding balance: ${loan.amount}",
                    notification_type='transaction'
                )
                
                print(f"Loan payment processed successfully for cheque {cheque_id} after 5-minute verification")
                
        except Exception as e:
            print(f"Error in delayed_loan_payment: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Start the thread
    thread = threading.Thread(target=delayed_loan_payment)
    thread.daemon = True
    thread.start()
    
    print(f"Scheduled loan payment approval for cheque {cheque_id} in 30 second")
    
    return True