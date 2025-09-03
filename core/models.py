from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Family(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)  # example field
    address = models.CharField(max_length=255)
    contactNo =models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Account(AbstractUser):
    account_id = models.AutoField(primary_key=True)  # primary key
    ROLE_CHOICES = [
        ('family', 'Family'),
        ('volunteer', 'Volunteer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='family')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

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
