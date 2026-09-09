from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin / Technical Supervisor'),
        ('INSPECTOR', 'Testing Person / Inspector'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='INSPECTOR')
    qualification = models.CharField(max_length=150, blank=True, default='ISO 9712 NDT Inspector Level II')
    certification_no = models.CharField(max_length=100, blank=True, default='CERT-99201')
    company_name = models.CharField(max_length=150, blank=True, default='MTQ Products B.V.')
    profile_signature = models.ImageField(upload_to='signatures/profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class InspectionProcedure(models.Model):
    title = models.CharField(max_length=200)
    standard_code = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_statement = models.TextField(
        default="This Gangway / Platform has been visually inspected in conformity with NEN-EN 526 and approved for use for the period of one year."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.standard_code})"

class NDTReport(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved / Passed'),
        ('REJECTED', 'Failed'),
    ]
    
    SIGNATURE_TYPE_CHOICES = [
        ('LIVE', 'Live Signature Canvas'),
        ('UPLOADED', 'Uploaded Signature File'),
        ('SAVED', 'Saved Profile Signature'),
    ]

    report_number = models.CharField(max_length=100, unique=True, help_text="e.g. MTQ-PR017Rev00")
    procedure = models.ForeignKey(InspectionProcedure, on_delete=models.SET_NULL, null=True, related_name='reports')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    vessel_name = models.CharField(max_length=200)
    project_no = models.CharField(max_length=100, help_text="MTQ Project No.")
    make_manufacturer = models.CharField(max_length=200, default="MTQ Products B.V.")
    year_manufactured = models.CharField(max_length=50, blank=True)
    size_length = models.CharField(max_length=100, blank=True, help_text="Size/length in meters")
    marking_tag = models.CharField(max_length=100, blank=True)
    
    inspection_date = models.DateField()
    validity_until = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED')
    approval_statement = models.TextField(
        default="This Gangway / Platform has been visually inspected in conformity with NEN-EN 526 and approved for use for the period of one year."
    )
    notes = models.TextField(blank=True, help_text="Additional observations or remarks")
    
    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPE_CHOICES, default='LIVE')
    signature_image = models.ImageField(upload_to='signatures/reports/', blank=True, null=True)
    stamp_image = models.ImageField(upload_to='stamps/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.vessel_name}"
