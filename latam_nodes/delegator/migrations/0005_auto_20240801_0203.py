# Generated by Django 3.2.19 on 2024-08-01 02:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('delegator', '0004_rename_week_balance_delegator_last_week_balance'),
    ]

    operations = [
        migrations.RenameField(
            model_name='delegator',
            old_name='last_week_balance',
            new_name='balance',
        ),
        migrations.RemoveField(
            model_name='delegator',
            name='total_balance',
        ),
    ]
