import random
import string
from .models import Jackpot, Ticket
from latam_nodes.delegator.models import Delegator
from django.db.models.signals import post_save
from django.db.models import Sum
from django.dispatch import receiver
from requests.sessions import Session



def generate_hash(length=4):
    characters = string.digits + string.ascii_uppercase
    hash_str = ''.join(random.choices(characters, k=length))
    return hash_str

@receiver(post_save, sender=Jackpot)
def create_ticket_from_jackpot(sender, instance, created, **kwargs):
    if created:
        # Delete all existing tickets
        Ticket.objects.all().delete()
        
        # Get all delegators with a non-zero last week balance
        delegators_have_week_balance = Delegator.objects.exclude(last_week_balance=0)
        # Calculate the total balance of all such delegators
        last_week_total_balance = delegators_have_week_balance.aggregate(total_balance=Sum('last_week_balance'))['total_balance']
        if last_week_total_balance is None:
            last_week_total_balance = 0
            
        total_ticket_count = int(last_week_total_balance // instance.ticket_cost) 
        # Create the required number of tickets
        for _ in range(total_ticket_count):
            while True:
                hash = generate_hash()
                if not Ticket.objects.filter(hash=hash).exists():
                    Ticket.objects.create(hash=hash)
                    break
        
        