from typing import Iterable
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from latam_nodes.base.models import BaseModel
from .utils import get_node_reward
from django.db import models


class Participant(BaseModel):
    address = models.CharField(max_length=100, primary_key=True)
    balance = models.DecimalField(max_digits=100, decimal_places=20, null=True)

    def __str__(self):
        return self.address


class Ticket(BaseModel):
    hash = models.CharField(max_length=4, primary_key=True)
    address = models.ForeignKey(
        Participant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets'
    )

    def __str__(self):
        return self.hash


class Jackpot(BaseModel):
    total_reward = models.DecimalField(
        max_digits=100,
        decimal_places=20,
        validators=[MinValueValidator(0)],
        null=True
    )
    current_reward = models.DecimalField(
        max_digits=100,
        decimal_places=20,
        validators=[MinValueValidator(0)],
        null=True
    )
    winning_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True
    )
    ticket_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    draw_date = models.DateTimeField(default=timezone.now)

    def formatted_date(self):
        return self.draw_date.strftime('%Y-%m-%d')

    def __str__(self):
        return f'{self.ticket_cost} - {self.draw_date}'
    
    def save(self, *args, **kwargs) -> None:
        current_reward = get_node_reward()
        previous_jackpots = Jackpot.objects.all().order_by("-created_at")
        if len(previous_jackpots) > 0:
            previous_total_reward = previous_jackpots[0].total_reward
            self.current_reward = abs(float(previous_total_reward) - current_reward)
        else:
            self.current_reward = current_reward
        self.total_reward = current_reward
        return super(Jackpot, self).save(*args, **kwargs)


class Winner(BaseModel):
    ticket_hash = models.CharField(max_length=4, blank=True, null=True)
    participant_address = models.CharField(max_length=100, blank=True, null=True)
    jackpot = models.ForeignKey(
        Jackpot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='winners'
    )

    def __str__(self):
        return f'{self.ticket_hash} - {self.participant_address} - {self.jackpot}'
