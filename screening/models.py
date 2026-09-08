from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=80, default='PHC Worker')
    department = models.CharField(max_length=100, default='PHC')
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_record')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_registered(self):
        return self.user_id is not None

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

class PHCWorker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phc_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    phc_name = models.CharField(max_length=100, default='Rampur')
    unit = models.CharField(max_length=100, default='Rural Health Screening Unit 01')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.phc_id})"

class Patient(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    patient_id = models.CharField(max_length=20, unique=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    diabetes_duration = models.DecimalField(max_digits=4, decimal_places=1, help_text="Years")
    hba1c = models.DecimalField(max_digits=4, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"

class Screening(models.Model):
    DR_STAGES = [
        ('0', 'No DR (Stage 0)'),
        ('1', 'Mild NPDR (Stage 1)'),
        ('2', 'Moderate NPDR (Stage 2)'),
        ('3', 'Severe NPDR (Stage 3)'),
        ('4', 'Proliferative DR (Stage 4)'),
    ]
    REFERRAL_URGENCY = [
        ('routine', 'Routine (12 Months)'),
        ('priority', 'Priority (3–4 Weeks)'),
        ('urgent', 'Urgent (< 7 Days)'),
    ]
    EYE_CHOICES = [('OD', 'Right Eye (OD)'), ('OS', 'Left Eye (OS)')]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='screenings')
    eye_side = models.CharField(max_length=2, choices=EYE_CHOICES)
    fundus_image = models.ImageField(upload_to='fundus/', null=True, blank=True)
    gradcam_image = models.ImageField(upload_to='gradcam/', null=True, blank=True)
    predicted_class = models.CharField(max_length=30, blank=True)
    dr_level = models.PositiveSmallIntegerField(default=0)
    ai_diagnosis = models.CharField(max_length=1, choices=DR_STAGES, default='0')
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    referable = models.BooleanField(default=False)
    low_confidence = models.BooleanField(default=False)
    quality_passed = models.BooleanField(default=False)
    quality_metrics = models.JSONField(default=dict)
    quality_message = models.CharField(max_length=255, blank=True)
    clinical_findings = models.JSONField(default=dict)  # e.g., {"microaneurysms": 14, "hemorrhages": "Multiple"}
    referral_urgency = models.CharField(max_length=10, choices=REFERRAL_URGENCY, default='routine')
    referral_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.get_ai_diagnosis_display()}"

class ReferralSlip(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE)
    slip_number = models.CharField(max_length=20, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)

    def __str__(self):
        return f"Slip {self.slip_number} for {self.screening.patient}"