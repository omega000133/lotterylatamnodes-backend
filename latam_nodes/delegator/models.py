from django.db import models
from django.core.validators import MinValueValidator


# Create your models here.

class Delegator(models.Model):
    address = models.CharField(max_length=100, primary_key=True)
    balance = models.FloatField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.address
