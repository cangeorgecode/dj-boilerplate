# Generated by Django 5.1.2 on 2024-10-19 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_subscription_billing_cycle_subscription_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]