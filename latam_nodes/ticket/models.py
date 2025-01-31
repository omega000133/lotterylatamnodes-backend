from django.core.validators import MaxValueValidator, MinValueValidator

from django.db import models
from django.utils import timezone

from latam_nodes.base.models import BaseModel


class Participant(BaseModel):
    address = models.CharField(max_length=100, primary_key=True)
    balance = models.DecimalField(max_digits=100, decimal_places=20, null=True)

    def __str__(self):
        return self.address


class Ticket(BaseModel):
    hash = models.CharField(max_length=4, primary_key=True)
    address = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    def __str__(self):
        return self.hash


class Jackpot(BaseModel):
    reward = models.DecimalField(
        max_digits=100, decimal_places=20, validators=[MinValueValidator(0)], null=True
    )
    reward_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
    )
    winning_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
    )
    start_distribute_time = models.IntegerField(
        validators=[MinValueValidator(5)], default=120
    )
    ticket_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    distributed_status = models.BooleanField(default=False)
    draw_date = models.DateTimeField(default=timezone.now)

    def formatted_date(self):
        return self.draw_date.strftime("%Y-%m-%d")

    def __str__(self):
        return f"{self.ticket_cost} - {self.draw_date}"


class Winner(BaseModel):
    ticket_hash = models.CharField(max_length=4, blank=True, null=True)
    closest_block_hash_date = models.DateTimeField(blank=True, null=True)
    participant_address = models.CharField(max_length=100, blank=True, null=True)
    jackpot = models.OneToOneField(
        Jackpot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="winners",
    )

    transaction = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.ticket_hash} - {self.participant_address} - {self.jackpot}"
