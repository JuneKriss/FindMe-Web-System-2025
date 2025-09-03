from django.db import models
from django.utils import timezone
from datetime import timedelta

class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    
    ROLE_CHOICES = [
        ('family', 'Family'),
        ('volunteer', 'Volunteer'),
        ('police', 'Police'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
class EmailVerificationCode(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5) 
    
class Family(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)  # example field
    address = models.CharField(max_length=255)
    contactNo =models.CharField(max_length=255)
    # account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="accounts")

    def __str__(self):
        return self.name
