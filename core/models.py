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
    full_name = models.CharField(max_length=255, null=True)
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
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_profile", null=True
    )
    address = models.CharField(max_length=255)
    contact_num = models.CharField(max_length=255)

    def __str__(self):
        return f"Family {self.family_id}"
    
class Volunteer(models.Model):
    volunteer_id = models.AutoField(primary_key=True)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='volunteer_profile', null=True
    )
    skills = models.CharField(max_length=255)
    availability = models.CharField(max_length=255)
    location_area = models.CharField(max_length=255)

    def __str__(self):
        return f"Volunteer {self.volunteer_id}"

class ReportCase(models.Model):
    report_id = models.AutoField(primary_key=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    full_name = models.CharField(max_length=255)
    age = models.PositiveBigIntegerField()
    gender = models.CharField(max_length=255)
    last_seen_date = models.DateField()
    last_seen_time = models.TimeField(null=True)        
    last_seen_location = models.CharField(max_length=255)
    clothing = models.CharField(max_length=255)
    notes = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Verified", "Verified"),
        ("In Progress", "In Progress"),
        ("On Hold", "On Hold"),
        ("Closed - Safe", "Closed - Safe"),
        ("Closed - Deceased", "Closed - Deceased"),
        ("Closed - Unresolved", "Closed - Unresolved"), 
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.status}"
    
class ReportAssistance(models.Model):
    assistance_id = models.AutoField(primary_key=True)
    report = models.ForeignKey(
        'ReportCase',
        on_delete=models.CASCADE,
        related_name='assistances'
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'volunteer'},
        related_name='volunteer_assistances'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('withdrawn', 'Withdrawn'),
        ],
        default='active',
    )

    class Meta:
        unique_together = ('report', 'volunteer')  # prevent duplicates

    def __str__(self):
        return f"{self.volunteer.full_name} assisting {self.report.full_name}"

class ReportMedia(models.Model):
    media_id = models.AutoField(primary_key=True)
    report = models.ForeignKey(ReportCase, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="report_media/")
    file_type = models.CharField(max_length=50, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media {self.media_id} for Report {self.report.report_id}"
    
class Notification(models.Model):
    ACTION_CHOICES = [
        ("report_created", "Report Created"),
        ("report_info_updated", "Report Information Updated"), 
        ("report_updated", "Report Updated (Sightings)"),
        ("status_changed", "Status Changed"),
        ("new_message", "New Message"),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    title = models.CharField(max_length=150)
    related_report = models.ForeignKey(
        ReportCase, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class UserNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_notifications"
    )
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="user_notifications"
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def mark_as_read(self):
        """Mark this notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_deleted(self):
        """Soft delete this notification (hide from user view)"""
        if not self.is_deleted:
            self.is_deleted = True
            self.save()

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
    
class ReportMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    report = models.ForeignKey('ReportCase', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Messages appear in order

    def __str__(self):
        return f"{self.sender.full_name}: {self.text[:30]}"
    
class ReportSighting(models.Model):
    sighting_id = models.AutoField(primary_key=True)
    report = models.ForeignKey('ReportCase', on_delete=models.CASCADE, related_name='sightings')
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'volunteer'},
        related_name='volunteer_sightings',
        null=True,  # ✅ ADD THIS
        blank=True,  # ✅ optional but good for admin
    )
    description = models.TextField()
    location = models.CharField(max_length=255)
    date_seen = models.DateField()
    time_seen = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sighting by {self.volunteer.full_name} on {self.date_seen}"
    
class SightingMedia(models.Model):
    media_id = models.AutoField(primary_key=True)
    sighting = models.ForeignKey(
        ReportSighting,
        on_delete=models.CASCADE,
        related_name="media"
    )
    file = models.FileField(upload_to="sighting_media/")
    file_type = models.CharField(max_length=50, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media {self.media_id} for Sighting {self.sighting.sighting_id}"
