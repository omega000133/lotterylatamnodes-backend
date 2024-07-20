from django.db import models


# Create your models here.

class Delegator(models.Model):
    address = models.CharField(max_length=100, primary_key=True)
    balance = models.DecimalField(max_digits=100, decimal_places=20)

    def __str__(self):
        return self.address
