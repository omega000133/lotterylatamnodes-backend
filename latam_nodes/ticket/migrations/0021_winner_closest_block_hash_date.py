# Generated by Django 3.2.19 on 2024-08-30 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0020_alter_jackpot_start_distribute_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='winner',
            name='closest_block_hash_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
