# screening/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Employee, PHCWorker

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_id', 'full_name', 'role', 'department', 'phone', 'email', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(),
        }

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    phone_number = forms.CharField(max_length=15, required=True)
    phc_id = forms.CharField(max_length=20, required=True, label="Employee ID")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password is None:
            return password
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:'\",.<>/?~`" for char in password):
            raise forms.ValidationError("Password must contain at least one special character.")
        return password

    def clean_phc_id(self):
        phc_id = self.cleaned_data.get('phc_id', '').strip()
        employee = Employee.objects.filter(employee_id__iexact=phc_id).first()
        if employee is None:
            raise forms.ValidationError('Invalid Employee ID. Please contact your administrator.')
        if not employee.is_active:
            raise forms.ValidationError('This Employee ID is inactive. Please contact your administrator.')
        if employee.user_id is not None:
            raise forms.ValidationError('This Employee ID is already registered.')
        return employee.employee_id

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        return phone

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username, email, or phone number", max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)