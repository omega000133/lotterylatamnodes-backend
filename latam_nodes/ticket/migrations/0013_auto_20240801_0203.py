# Generated by Django 3.2.19 on 2024-08-01 02:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0012_auto_20240725_2224'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jackpot',
            old_name='current_reward',
            new_name='reward',
        ),
        migrations.RemoveField(
            model_name='jackpot',
            name='total_reward',
        ),
    ]
