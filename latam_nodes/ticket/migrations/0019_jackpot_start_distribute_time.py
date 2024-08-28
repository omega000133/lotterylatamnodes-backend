# Generated by Django 3.2.19 on 2024-08-26 14:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ticket", "0018_alter_winner_jackpot"),
    ]

    operations = [
        migrations.AddField(
            model_name="jackpot",
            name="start_distribute_time",
            field=models.IntegerField(
                default=120, validators=[django.core.validators.MinValueValidator(40)]
            ),
        ),
    ]