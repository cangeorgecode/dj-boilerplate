# Generated by Django 5.1.2 on 2024-10-30 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_customuser_stripe_customer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='is_lifetime',
            field=models.BooleanField(default=False),
        ),
    ]
