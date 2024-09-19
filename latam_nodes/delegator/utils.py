from django.db.models import Sum
from .models import Delegator

def get_total_delegation_amount():
    total_amount_of_delegation = Delegator.objects.aggregate(total_balance=Sum("balance"))[
        "total_balance"
    ]
    if total_amount_of_delegation is None:
        total_amount_of_delegation = 0  # Handle cases where no balance is available
        
    return total_amount_of_delegation