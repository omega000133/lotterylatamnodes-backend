import random
import string
from .models import Jackpot, Ticket
from latam_nodes.delegator.models import Delegator
from django.db.models.signals import post_save
from django.db.models import Sum
from django.dispatch import receiver
from requests.sessions import Session
from .utils import get_node_reward


def generate_hash(length=4):
    characters = string.digits + string.ascii_uppercase
    hash_str = ''.join(random.choices(characters, k=length))
    return hash_str

@receiver(post_save, sender=Jackpot)
def create_ticket_from_jackpot(sender, instance, created, **kwargs):
    if created:
        current_reward = get_node_reward()
        instance.reward = current_reward
        
        instance.save()
        
        # Get all delegators with a non-zero last week balance
        delegators_balance = Delegator.objects.exclude(balance=0)
        # Calculate the total balance of all such delegators
        total_balance = delegators_balance.aggregate(total_balance=Sum('balance'))['total_balance']
        if total_balance is None:
            total_balance = 0
            
        total_ticket_count = int(float(total_balance) // float(instance.ticket_cost))
        max_ticket_count = 36 ** 4
        if total_ticket_count > max_ticket_count:
            total_ticket_count = max_ticket_count
        # Create the required number of tickets
        unique_hashes = set()
        while len(unique_hashes) < total_ticket_count:
            hash = generate_hash()
            unique_hashes.add(hash)
                
        Ticket.objects.all().delete()
        tickets = [Ticket(hash=hash) for hash in unique_hashes]
        Ticket.objects.bulk_create(tickets, ignore_conflicts=True)
        
        