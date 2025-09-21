from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.conf import settings
class Account(AbstractUser):
    account_id = models.AutoField(primary_key=True)  # primary key
    role = models.CharField(max_length=20, choices=[
        ('family', 'Family'),
        ('volunteer', 'Volunteer'),
        ('police', 'Police'),
    ], default='user')
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

    # Optional: keep this if you want `user.id` to return account_id
    @property
    def id(self):
        return self.account_id
    

class ReportCase(models.Model):
    report_id = models.AutoField(primary_key=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    full_name = models.CharField(max_length=255)
    age = models.PositiveBigIntegerField()
    gender =models.CharField(max_length=255)
    last_seen_date = models.DateField()
    last_seen_time = models.TimeField(null=True)
    last_seen_location = models.CharField(max_length=255)
    clothing = models.CharField(max_length=255)
    notes = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[("Missing", "Missing"), ("Ongoing", "Ongoing"), ("Resolved", "Resolved")],
        default="Missing",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.status}"
