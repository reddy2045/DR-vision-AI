import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
from pathlib import Path
from uuid import uuid4
import jwt
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Patient, Screening, PHCWorker
from .models import Employee
from ai_engine.matlab_engine import MATLABConfigurationError, MATLABEngineUnavailable
from ai_engine.predictor import predict_fundus
from ai_engine.quality import MAX_IMAGE_BYTES, check_image_quality

logger = logging.getLogger(__name__)


def _jwt_payload(user):
    return {
        'sub': str(user.id),
        'employee_id': getattr(getattr(user, 'employee_record', None), 'employee_id', user.username),
        'role': 'admin' if user.is_staff else 'PHC Worker',
        'exp': datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRES_HOURS),
    }


def api_jwt_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token is required.'}, status=401)
        try:
            claims = jwt.decode(header[7:], settings.JWT_SECRET, algorithms=['HS256'])
            user = User.objects.get(id=int(claims['sub']), is_active=True)
        except (jwt.InvalidTokenError, User.DoesNotExist, KeyError):
            return JsonResponse({'error': 'Invalid or expired token.'}, status=401)
        request.user = user
        return view(request, *args, **kwargs)
    return wrapped


def _api_user(user):
    employee = getattr(user, 'employee_record', None)
    return {
        'id': user.id,
        'employee_id': employee.employee_id if employee else user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': 'admin' if user.is_staff else 'PHC Worker',
    }

# ----- API views -----

@api_jwt_required
def api_patients(request):
    patients = Patient.objects.all().values('id', 'first_name', 'last_name', 'patient_id', 'age', 'gender')
    return JsonResponse(list(patients), safe=False)

@api_jwt_required
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

@csrf_exempt
@api_jwt_required
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
            fundus_image.name = f'{uuid4().hex}{suffix}'
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
        logger.exception('Screening failed')
        if screening and screening.fundus_image:
            screening.fundus_image.delete(save=False)
        public_message = getattr(e, 'public_message', str(e))
        status = 503 if isinstance(e, (MATLABConfigurationError, MATLABEngineUnavailable)) else 400
        return JsonResponse({'error': public_message}, status=status)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)

@api_jwt_required
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


@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    login_value = str(data.get('login', '')).strip()
    password = str(data.get('password', ''))
    user = User.objects.filter(username=login_value).first() or User.objects.filter(email__iexact=login_value).first()
    if user is None:
        employee = Employee.objects.filter(employee_id=login_value).select_related('user').first()
        user = employee.user if employee else None
    if user is None or not user.is_active or not user.check_password(password):
        return JsonResponse({'error': 'Invalid credentials.'}, status=401)
    safe_user = _api_user(user)
    return JsonResponse({'user': safe_user, 'token': jwt.encode(_jwt_payload(user), settings.JWT_SECRET, algorithm='HS256')})


@csrf_exempt
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    employee_id = str(data.get('employee_id', '')).strip()
    full_name = str(data.get('full_name', '')).strip()
    email = str(data.get('email', '')).strip()
    password = str(data.get('password', ''))
    if not employee_id or not full_name or not email or len(password) < 8:
        return JsonResponse({'error': 'employee_id, full_name, email and an 8-character password are required.'}, status=400)

    employee = Employee.objects.filter(employee_id__iexact=employee_id).first()
    if employee is None:
        return JsonResponse({'error': 'Invalid Employee ID. Please contact your administrator.'}, status=400)
    if not employee.is_active:
        return JsonResponse({'error': 'This Employee ID is inactive. Please contact your administrator.'}, status=403)
    if employee.user_id is not None:
        return JsonResponse({'error': 'This Employee ID is already registered.'}, status=409)
    if User.objects.filter(username=employee.employee_id).exists() or User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'error': 'An account with this employee ID or email already exists.'}, status=409)
    first_name, _, last_name = full_name.partition(' ')
    with transaction.atomic():
        user = User.objects.create_user(username=employee.employee_id, first_name=first_name, last_name=last_name, email=email, password=password)
        employee.user = user
        employee.full_name = full_name
        employee.email = email
        employee.save(update_fields=['user', 'full_name', 'email', 'updated_at'])
        PHCWorker.objects.create(user=user, phc_id=employee.employee_id, phone_number=employee.phone or None)
    safe_user = _api_user(user)
    return JsonResponse({'user': safe_user, 'token': jwt.encode(_jwt_payload(user), settings.JWT_SECRET, algorithm='HS256')}, status=201)


def api_staff_required(view):
    @wraps(view)
    @api_jwt_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Administrator access is required.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapped


def _employee_payload(employee):
    return {
        'id': employee.id,
        'employee_id': employee.employee_id,
        'full_name': employee.full_name,
        'role': employee.role,
        'department': employee.department,
        'phone': employee.phone,
        'email': employee.email,
        'is_active': employee.is_active,
        'is_registered': employee.is_registered,
        'created_at': employee.created_at.isoformat(),
    }


@csrf_exempt
@api_staff_required
def api_admin_employees(request, employee_id=None):
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        status = request.GET.get('status', '')
        employees = Employee.objects.select_related('user').order_by('employee_id')
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
        if status == 'registered':
            employees = employees.filter(user__isnull=False)
        elif status == 'pending':
            employees = employees.filter(user__isnull=True)
        all_employees = Employee.objects.all()
        return JsonResponse({
            'employees': [_employee_payload(employee) for employee in employees],
            'stats': {
                'total': all_employees.count(),
                'active': all_employees.filter(is_active=True).count(),
                'inactive': all_employees.filter(is_active=False).count(),
                'registered': all_employees.filter(user__isnull=False).count(),
                'pending': all_employees.filter(user__isnull=True).count(),
            },
        })

    if request.method not in ('POST', 'PUT', 'PATCH'):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    employee = get_object_or_404(Employee, pk=employee_id) if employee_id else None
    values = {
        'employee_id': str(data.get('employee_id', employee.employee_id if employee else '')).strip(),
        'full_name': str(data.get('full_name', employee.full_name if employee else '')).strip(),
        'role': str(data.get('role', employee.role if employee else 'PHC Worker')).strip(),
        'department': str(data.get('department', employee.department if employee else 'PHC')).strip(),
        'phone': str(data.get('phone', employee.phone if employee else '')).strip(),
        'email': str(data.get('email', employee.email if employee else '')).strip(),
        'is_active': data.get('is_active', employee.is_active if employee else True),
    }
    if not values['employee_id'] or not values['full_name']:
        return JsonResponse({'error': 'Employee ID and full name are required.'}, status=400)
    duplicate = Employee.objects.filter(employee_id=values['employee_id']).exclude(pk=employee.pk if employee else None).exists()
    if duplicate:
        return JsonResponse({'error': 'That employee ID already exists.'}, status=409)
    if employee is None:
        employee = Employee.objects.create(**values)
        status_code = 201
    else:
        for field, value in values.items():
            setattr(employee, field, value)
        employee.save()
        if employee.user_id:
            employee.user.is_active = employee.is_active
            employee.user.save(update_fields=['is_active'])
        status_code = 200
    return JsonResponse({'employee': _employee_payload(employee)}, status=status_code)

