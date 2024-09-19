from django import forms
from .models import Jackpot
from .utils import get_total_ticket_count
from latam_nodes.delegator.utils import get_total_delegation_amount

class JackpotForm(forms.ModelForm):
    class Meta:
        model = Jackpot
        fields = '__all__'

    def clean_ticket_cost(self):
        ticket_cost = self.cleaned_data.get('ticket_cost')
        total_delegation_amount = get_total_delegation_amount()
        ticket_number = get_total_ticket_count()
        
        if total_delegation_amount == 0 or ticket_number == 0:
            raise forms.ValidationError("There are no ticker or no delegator. To create jackpot, please check ticket and delegators.")
          
        calculate_ticket_cost = round(total_delegation_amount / ticket_number, 1)
        
        if ticket_cost is None or ticket_cost < calculate_ticket_cost:
            raise forms.ValidationError(f"Currently total delegation amount is { round(total_delegation_amount, 1) } and total ticket number is { ticket_number }. So you should set ticket cost to more than { calculate_ticket_cost }")
          
        return ticket_cost
