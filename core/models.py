from django.db import models

class Family(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)  # example field
    address = models.CharField(max_length=255)
    contactNo =models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # store hashed passwords!
    email = models.EmailField(unique=True)
    
    ROLE_CHOICES = [
        ('family', 'Family'),
        ('volunteer', 'Volunteer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    
    # family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="accounts")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username