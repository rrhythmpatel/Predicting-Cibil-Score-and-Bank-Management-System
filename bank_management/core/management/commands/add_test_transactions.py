from django.core.management.base import BaseCommand
from core.models import User, Transaction  # Update to import User from core.models
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Add test transaction data'

    def handle(self, *args, **kwargs):
        # Create test users with required fields
        user1, _ = User.objects.get_or_create(
            username='testuser1',
            defaults={
                'email': 'testuser1@example.com',
                'password': 'testpass123',
                'is_active': True
            }
        )
        user2, _ = User.objects.get_or_create(
            username='testuser2',
            defaults={
                'email': 'testuser2@example.com',
                'password': 'testpass123',
                'is_active': True
            }
        )

        # Set passwords properly for test users
        if _:  # If user was created
            user1.set_password('testpass123')
            user2.set_password('testpass123')
            user1.save()
            user2.save()

        # Create transactions for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        current_date = start_date
        while current_date <= end_date:
            # Create 1-5 transactions per day
            for _ in range(random.randint(1, 5)):
                amount = random.randint(100, 1000)
                Transaction.objects.create(
                    sender=user1,
                    recipient=user2,
                    amount=amount,
                    timestamp=current_date
                )
            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS('Successfully added test transactions'))