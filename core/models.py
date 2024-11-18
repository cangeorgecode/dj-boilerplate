from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    bio = models.TextField(blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username

class Subscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'basic_monthly', 'premium_annually'
    billing_cycle = models.CharField(max_length=10, null=True, blank=True)  # e.g., 'monthly', 'annually'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_lifetime = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.plan} ({self.billing_cycle})"