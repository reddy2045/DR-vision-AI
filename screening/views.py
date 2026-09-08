import json
import logging
import os
import tempfile
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Patient, Screening, PHCWorker
from .models import Employee
from .forms import EmployeeForm, RegistrationForm, LoginForm
from ai_engine.predictor import predict_fundus
from ai_engine.quality import MAX_IMAGE_BYTES, check_image_quality

logger = logging.getLogger(__name__)

# ----- Dashboard and API views -----

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def api_patients(request):
    patients = Patient.objects.all().values('id', 'first_name', 'last_name', 'patient_id', 'age', 'gender')
    return JsonResponse(list(patients), safe=False)

@login_required
def api_screening(request, patient_id):
    try:
        patient = Patient.objects.get(patient_id=patient_id)
        screening = patient.screenings.order_by('-created_at').first()
        if screening:
            data = {
                'screening_id': screening.id,
                'screening_date': screening.created_at.isoformat(),
                'patient_name': f"{patient.first_name} {patient.last_name}",
                'patient_id': patient.patient_id,
                'age': patient.age,
                'gender': patient.get_gender_display(),
                'diabetes_duration': patient.diabetes_duration,
                'hba1c': float(patient.hba1c),
                'eye_side': screening.get_eye_side_display(),
                'ai_diagnosis': screening.get_ai_diagnosis_display(),
                'predicted_class': screening.predicted_class,
                'dr_level': screening.dr_level,
                'confidence': float(screening.confidence),
                'referable': screening.referable,
                'low_confidence': screening.low_confidence,
                'quality_passed': screening.quality_passed,
                'quality_metrics': screening.quality_metrics,
                'quality_message': screening.quality_message,
                'findings': screening.clinical_findings,
                'referral_urgency': screening.referral_urgency,
                'referral_urgency_display': screening.get_referral_urgency_display(),
                'image_url': screening.fundus_image.url if screening.fundus_image else None,
                'gradcam_url': screening.gradcam_image.url if screening.gradcam_image else None,
                'fov': '45°',
                'resolution': '1536×1536',
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'No screening found'}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

@login_required
def api_create_screening(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    temporary_path = None
    screening = None
    try:
        # Handle both JSON and FormData
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            return JsonResponse({'error': 'fundus_image is required.'}, status=400)
        else:
            data = request.POST.dict()
            fundus_image = request.FILES.get('fundus_image')

        if fundus_image is None:
            return JsonResponse({'error': 'fundus_image is required.'}, status=400)
        if fundus_image.size > MAX_IMAGE_BYTES:
            return JsonResponse({'error': 'Image is too large. Maximum size is 10 MB.'}, status=400)

        suffix = Path(fundus_image.name).suffix.lower()
        if suffix not in {'.jpg', '.jpeg', '.png'}:
            return JsonResponse({'error': 'Only JPG, JPEG, and PNG images are supported.'}, status=400)

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            for chunk in fundus_image.chunks():
                temporary_file.write(chunk)
            temporary_path = temporary_file.name

        quality = check_image_quality(temporary_path)
        if not quality['passed']:
            return JsonResponse({
                'error': quality['message'],
                'quality_metrics': quality.get('metrics', {}),
            }, status=422)

        # ---------- Fix: handle full name from frontend ----------
        # Frontend sends 'patientName' as full name, or 'first_name'/'last_name'
        full_name = data.get('patientName') or data.get('first_name')
        if full_name:
            parts = full_name.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
        else:
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')

        # If still empty, raise error
        if not first_name:
            return JsonResponse({'error': 'Patient first name is required'}, status=400)

        with transaction.atomic():
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                patient_id=data.get('patient_id'),
                age=int(data.get('age', 0)),
                gender=data.get('gender', 'M'),
                diabetes_duration=Decimal(str(data.get('diabetes_duration', '0'))),
                hba1c=float(data.get('hba1c', 0.0))
            )
            screening = Screening.objects.create(
                patient=patient,
                eye_side=data.get('eye_side', 'OD'),
                fundus_image=fundus_image,
                quality_passed=True,
                quality_metrics=quality['metrics'],
                quality_message=quality['message'],
            )
            ai_result = predict_fundus(screening.fundus_image.path)
            screening.predicted_class = ai_result['predicted_class']
            screening.dr_level = ai_result['dr_level']
            screening.ai_diagnosis = str(ai_result['dr_level'])
            screening.confidence = ai_result['confidence']
            screening.referable = ai_result['referable']
            screening.low_confidence = ai_result['low_confidence']
            screening.referral_urgency = ai_result['referral_urgency']
            screening.clinical_findings = {}
            gradcam_path = ai_result.get('gradcam_path')
            if gradcam_path and os.path.isfile(gradcam_path):
                relative_gradcam = os.path.relpath(gradcam_path, settings.MEDIA_ROOT).replace(os.sep, '/')
                screening.gradcam_image.name = relative_gradcam
            screening.save()

            logger.info(
                'Screening completed patient_id=%s screening_id=%s image=%s '
                'predicted_class=%s confidence=%.2f dr_level=%s referable=%s '
                'referral_urgency=%s low_confidence=%s',
                patient.patient_id,
                screening.id,
                screening.fundus_image.path,
                screening.predicted_class,
                float(screening.confidence),
                screening.dr_level,
                screening.referable,
                screening.referral_urgency,
                screening.low_confidence,
            )

        return JsonResponse({
            'id': screening.id,
            'screening_id': screening.id,
            'screening_date': screening.created_at.isoformat(),
            'patient_id': patient.patient_id,
            'image_url': screening.fundus_image.url if screening.fundus_image else None,
            'gradcam_url': screening.gradcam_image.url if screening.gradcam_image else None,
            'predicted_class': screening.predicted_class,
            'dr_level': screening.dr_level,
            'confidence': float(screening.confidence),
            'referable': screening.referable,
            'referral_urgency': screening.referral_urgency,
            'referral_urgency_display': screening.get_referral_urgency_display(),
            'low_confidence': screening.low_confidence,
        })

    except Exception as e:
        if screening and screening.fundus_image:
            screening.fundus_image.delete(save=False)
        return JsonResponse({'error': str(e)}, status=400)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)

@login_required
def api_generate_referral(request, screening_id):
    try:
        screening = Screening.objects.get(id=screening_id)
        return JsonResponse({
            'message': 'Referral generated',
            'slip_number': f'REF-{screening.id:04d}',
            'screening_id': screening.id,
            'screening_date': screening.created_at.isoformat(),
            'patient_name': f'{screening.patient.first_name} {screening.patient.last_name}'.strip(),
            'patient_id': screening.patient.patient_id,
            'age': screening.patient.age,
            'gender': screening.patient.get_gender_display(),
            'diabetes_duration': screening.patient.diabetes_duration,
            'hba1c': float(screening.patient.hba1c),
            'eye_side': screening.get_eye_side_display(),
            'predicted_class': screening.predicted_class,
            'dr_level': screening.dr_level,
            'confidence': float(screening.confidence),
            'referable': screening.referable,
            'low_confidence': screening.low_confidence,
            'quality_passed': screening.quality_passed,
            'quality_metrics': screening.quality_metrics,
            'quality_message': screening.quality_message,
            'referral_urgency': screening.referral_urgency,
            'referral_urgency_display': screening.get_referral_urgency_display(),
            'gradcam_url': screening.gradcam_image.url if screening.gradcam_image else None,
        })
    except Screening.DoesNotExist:
        return JsonResponse({'error': 'Screening not found'}, status=404)

# ----- Authentication views -----

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            phc_id = form.cleaned_data['phc_id']
            phone_number = form.cleaned_data['phone_number']
            employee = Employee.objects.get(employee_id=phc_id)

            with transaction.atomic():
                user = User.objects.create_user(
                    username=phc_id,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data.get('last_name', ''),
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                employee.user = user
                employee.phone = phone_number
                employee.email = form.cleaned_data['email']
                employee.full_name = f"{user.first_name} {user.last_name}".strip()
                employee.save(update_fields=['user', 'phone', 'email', 'full_name', 'updated_at'])
                PHCWorker.objects.create(
                    user=user,
                    phc_id=phc_id,
                    phone_number=phone_number
                )
                success_message = "Registration successful. Please log in."
            messages.success(request, success_message)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('admin_dashboard' if user.is_staff else 'dashboard')
            else:
                messages.error(request, "Invalid credentials.")
        else:
            username = request.POST.get('username', '').strip()
            inactive_user = User.objects.filter(username=username, is_active=False).first()
            if inactive_user is None:
                inactive_user = User.objects.filter(email__iexact=username, is_active=False).first()
            if inactive_user is None:
                worker = PHCWorker.objects.filter(phc_id=username).select_related('user').first()
                if worker and not worker.user.is_active:
                    inactive_user = worker.user
            if inactive_user is None:
                worker = PHCWorker.objects.filter(phone_number=username).select_related('user').first()
                if worker and not worker.user.is_active:
                    inactive_user = worker.user
            messages.error(request, 'Account is inactive.' if inactive_user else 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


def staff_required(view):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url='admin_login',
    )(view)


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Administrator access is required.')
    return render(request, 'registration/admin_login.html', {'form': form})


@staff_required
def admin_dashboard(request):
    employees = Employee.objects.select_related('user').order_by('employee_id')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    registration = request.GET.get('registration', '')
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) |
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    if status == 'active':
        employees = employees.filter(is_active=True)
    elif status == 'inactive':
        employees = employees.filter(is_active=False)
    if registration == 'registered':
        employees = employees.filter(user__isnull=False)
    elif registration == 'pending':
        employees = employees.filter(user__isnull=True)
    all_employees = Employee.objects.all()
    context = {
        'employees': employees,
        'total_employees': all_employees.count(),
        'active_employees': all_employees.filter(is_active=True).count(),
        'inactive_employees': all_employees.filter(is_active=False).count(),
        'registered_employees': all_employees.filter(user__isnull=False).count(),
        'pending_employees': all_employees.filter(user__isnull=True).count(),
        'query': query,
        'status': status,
        'registration': registration,
    }
    return render(request, 'admin_dashboard.html', context)


@staff_required
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Employee ID created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'employee_form.html', {'form': form, 'title': 'Add Employee'})


@staff_required
def employee_edit(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == 'POST' and form.is_valid():
        employee = form.save()
        if employee.user_id:
            employee.user.is_active = employee.is_active
            employee.user.save(update_fields=['is_active'])
        messages.success(request, 'Employee details updated.')
        return redirect('admin_dashboard')
    return render(request, 'employee_form.html', {'form': form, 'title': 'Edit Employee', 'employee': employee})


@staff_required
def employee_toggle_status(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        employee.is_active = not employee.is_active
        employee.save(update_fields=['is_active', 'updated_at'])
        if employee.user:
            employee.user.is_active = employee.is_active
            employee.user.save(update_fields=['is_active'])
        status_str = "activated" if employee.is_active else "deactivated"
        messages.success(request, f"Employee {employee.employee_id} has been {status_str}.")
    return redirect('admin_dashboard')