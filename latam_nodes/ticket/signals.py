from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Jackpot, Participant, Ticket
from .utils import get_node_reward


@receiver(post_save, sender=Jackpot)
def create_ticket_from_jackpot(sender, instance, created, **kwargs):
    if created:
        current_reward = get_node_reward()
        instance.reward = current_reward

        instance.save()

        activated_tickets = Ticket.objects.filter(address__isnull=False)
        activated_tickets.update(address=None)
        Participant.objects.update(is_active=False)
