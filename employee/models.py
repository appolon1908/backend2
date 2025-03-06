import uuid
import string
import random
from django.db import models
# from django.contrib.auth.models import User
from auth_app.models import User




def generate_id():
    return uuid.uuid4().hex

def generate_employee_id():
    return ''.join(random.choices(string.digits, k=6))


TEAM_PREFIXES = {
    'dev team': 'DV_',
    'design team': 'DS_',
    'biz dev team': 'BZ_',
    'test team': 'TS_',
    'mkt team': 'MK_',
    'tech team': 'TC_'
}

def generate_employee_id_with_prefix(team):
    if not team:  # Check if team is None or empty
        prefix = 'XX_'  # Default prefix for missing team
    else:
        prefix = TEAM_PREFIXES.get(team.lower(), team[:2].upper() + '_')
    return prefix + ''.join(random.choices(string.digits, k=6))

class Employee(models.Model):
    id = models.CharField(primary_key=True, editable=False, default=generate_id, max_length=70)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile/images/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    country = models.CharField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    team = models.CharField(max_length=256, null=True, blank=True)
    role = models.CharField(max_length=256, null=True, blank=True)
    employee_id = models.CharField(max_length=256, editable=False, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    extra_fields = models.JSONField(verbose_name="extra-fields", default=dict, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Only generate employee_id if it's not already set
        if not self.employee_id and self.team:
            self.employee_id = generate_employee_id_with_prefix(self.team)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.first_name + " " + self.last_name
    
    

class SocialMedia(models.Model):
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="social_media_profiles"
    )
    name = models.CharField(max_length=100)  # e.g., Instagram, Twitter
    link = models.URLField()  # e.g., https://instagram.com/username

    def __str__(self):
        return f"{self.name} - {self.employee.first_name} {self.employee.last_name}"
    
    


