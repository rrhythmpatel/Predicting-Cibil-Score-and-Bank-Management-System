from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChequeDeposit, Transaction, Notification
from django.db import transaction

def auto_approve_cheque(cheque_id, user_id, amount):
    """
    Automatically approve a cheque deposit and credit the user's account
    """
    try:
        # Use transaction atomic to ensure database consistency
        with transaction.atomic():
            # Get the user
            User = get_user_model()
            user = User.objects.select_for_update().get(id=user_id)
            
            # Get the cheque deposit
            cheque = ChequeDeposit.objects.select_for_update().get(id=cheque_id)
            
            # Check if the cheque is still pending
            if cheque.status != 'pending':
                print(f"Cheque {cheque_id} is no longer pending, status: {cheque.status}")
                return False
            
            # Update deposit status
            cheque.status = 'approved'
            cheque.approved_date = timezone.now()
            cheque.save()
            
            # Convert amount to Decimal if it's not already
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            # Store the old balance for logging
            old_balance = user.account_balance
            
            # Credit the user's account
            user.account_balance += amount
            user.save()
            
            print(f"User balance before: {old_balance}")
            print(f"Amount credited: {amount}")
            print(f"User balance after: {user.account_balance}")
            
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                sender=None,  # System transaction
                recipient=user,
                amount=amount,
                transaction_type='CHEQUE_DEPOSIT',
                status='COMPLETED',
                reference_number=f"CHEQUE-{cheque.cheque_number}",
                description=f"Cheque deposit from {cheque.bank_name}, Cheque #{cheque.cheque_number}"
            )
            
            # Create notification for the user
            Notification.objects.create(
                user=user,
                message=f"Your cheque deposit of ${amount} has been approved and credited to your account.",
                notification_type='transaction'
            )
            
            print(f"Automatically approved cheque deposit {cheque_id} for user {user.username}, amount: ${amount}")
            print(f"Transaction created: {transaction_obj.id}")
            return True
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in automatic cheque approval for cheque {cheque_id}: {str(e)}")
        return False