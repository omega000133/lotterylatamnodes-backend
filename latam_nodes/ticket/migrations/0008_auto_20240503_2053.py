# Generated by Django 3.2.19 on 2024-05-03 20:53

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0007_jackpot_ticket_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='jackpot',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jackpot',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='jackpot',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
