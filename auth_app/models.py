import uuid
from django.db import models

from user_agents import parse
from datetime import timedelta
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin




class UserManager(BaseUserManager):
    """
    Custom manager for User model with no username field.
    Methods
    -------
    _create_user(email, password, **extra_fields)
        Creates and saves a User with the given email and password.
    create_user(email, password=None, **extrafields)
        Creates and saves a regular User with the given email and password.
    create_superuser(email, password=None, **extrafields)
        Creates and saves a superuser with the given email and password.
    """
    
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = True # bad practice, remove later
        user.save()
        return user

    def create_user(self, email, password=None, **extrafields):
        extrafields.setdefault("is_superuser", False)
        return self._create_user(email=email, password=password, **extrafields)

    def create_superuser(self, email, password=None, **extrafields):
        extrafields.setdefault("is_superuser", True)
        extrafields.setdefault("is_active", True)
        extrafields.setdefault("is_staff", True)
        return self._create_user(email=email, password=password, **extrafields)



def generate_id():
    return uuid.uuid4().hex

def set_trial_expiry_date():
    return now() + timedelta(days=7)

def generate_client_id():
    return uuid.uuid4().hex[:6]

class User(AbstractBaseUser, PermissionsMixin):
    """ 
    User Model
    
    To be used for authentication and authorization
    
    Remaining Fields:
	•	Roles and Permissions:
	•	role (e.g., admin, editor, viewer)
	•	organization_id (for teams and companies)
	•	permissions (granular access levels, such as posting, scheduling, or viewing analytics)
	
    """
    
    
    FREE = 'FREE'
    PROFESSIONAL = 'PROFESSIONAL'
    TEAM = 'TEAM'
    ENTERPRISE = 'ENTERPRISE'
    
    PLAN_TYPE = [
        (FREE, 'Free'),
        (PROFESSIONAL, 'Professional'),
        (TEAM, 'Team'),
        (ENTERPRISE, 'Enterprise'),
    ]
    
    
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    client_id = models.CharField(max_length=256, blank=True, null=True, default=generate_client_id)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='users/profile_pictures/', blank=True, null=True)
    timezone = models.CharField(max_length=100, default='UTC', null=True, blank=True)
    #id asigned by odoo to identify the costumer or client there.
    odoo_id = models.IntegerField(null=True, blank=True)
    # Subscription Information
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE, default=FREE)
    # billing_status TBD
    # trial_expiry_date TBD
    trial_expiry_date = models.DateTimeField(blank=True, null=True, default=set_trial_expiry_date)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = UserManager()

    REQUIRED_FIELDS = []
    USERNAME_FIELD = "email"
    

    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.display_name
    
    



class Visitor(models.Model):
    ip_address = models.GenericIPAddressField()
    page = models.URLField(default="https://codestra.co")
    device = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    browser = models.CharField(max_length=100)
    method = models.CharField(max_length=10, default='GET', blank=True, null=True) #HTTPS Method called
    visited_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.ip_address} visited {self.page} on {self.visited_at}"




class BlacklistedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted IP: {self.ip_address}"
