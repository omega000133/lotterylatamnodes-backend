# Generated by Django 3.2.19 on 2024-04-23 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0003_auto_20240419_2255'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='id',
        ),
        migrations.AlterField(
            model_name='ticket',
            name='hash',
            field=models.CharField(max_length=4, primary_key=True, serialize=False),
        ),
    ]
