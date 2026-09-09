import base64
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from .models import NDTReport, InspectionProcedure, UserProfile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    total_reports = NDTReport.objects.count()
    approved_reports = NDTReport.objects.filter(status='APPROVED').count()
    vessels_count = NDTReport.objects.values('vessel_name').distinct().count()
    procedures_count = InspectionProcedure.objects.count()
    
    if profile.role == 'ADMIN':
        recent_reports = NDTReport.objects.all().select_related('inspector', 'procedure')[:8]
    else:
        recent_reports = NDTReport.objects.filter(inspector=user).select_related('inspector', 'procedure')[:8]
        
    context = {
        'profile': profile,
        'total_reports': total_reports,
        'approved_reports': approved_reports,
        'vessels_count': vessels_count,
        'procedures_count': procedures_count,
        'recent_reports': recent_reports,
    }
    return render(request, 'dashboard.html', context)

@login_required
def report_list(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    reports = NDTReport.objects.all().select_related('inspector', 'procedure')
    
    if profile.role != 'ADMIN':
        reports = reports.filter(inspector=request.user)
        
    if search_query:
        reports = reports.filter(
            Q(report_number__icontains=search_query) |
            Q(vessel_name__icontains=search_query) |
            Q(project_no__icontains=search_query) |
            Q(marking_tag__icontains=search_query)
        )
        
    if status_filter:
        reports = reports.filter(status=status_filter)
        
    context = {
        'reports': reports,
        'search_query': search_query,
        'status_filter': status_filter,
        'profile': profile,
    }
    return render(request, 'report_list.html', context)

from django.http import JsonResponse

def generate_unique_report_number():
    count = NDTReport.objects.count() + 17
    num_str = f"MTQ-PR{count:03d}Rev00"
    while NDTReport.objects.filter(report_number=num_str).exists():
        count += 1
        num_str = f"MTQ-PR{count:03d}Rev00"
    return num_str

@login_required
def check_report_number(request):
    report_num = request.GET.get('report_number', '').strip()
    current_id = request.GET.get('current_id', None)
    
    if not report_num:
        return JsonResponse({'available': False, 'message': 'Certificate number cannot be empty.'})
        
    query = NDTReport.objects.filter(report_number__iexact=report_num)
    if current_id and current_id.isdigit():
        query = query.exclude(pk=int(current_id))
        
    if query.exists():
        return JsonResponse({
            'available': False, 
            'message': f"Certificate number '{report_num}' is already in use by another certificate."
        })
    else:
        return JsonResponse({
            'available': True, 
            'message': f"Certificate number '{report_num}' is available."
        })

@login_required
def create_report(request):
    procedures = InspectionProcedure.objects.all()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    procedure_id = request.GET.get('procedure_id') if request.method == 'GET' else request.POST.get('procedure_id')
    
    # If GET request and no procedure selected initially, render the certificate selection cards!
    if request.method == 'GET' and not procedure_id:
        return render(request, 'select_certificate.html', {'procedures': procedures, 'profile': profile})
        
    if procedure_id:
        selected_procedure = get_object_or_404(InspectionProcedure, id=procedure_id)
        # Check if disabled
        is_gangway = selected_procedure.standard_code == "EN 526:2016" or "gangway" in selected_procedure.title.lower()
        if not is_gangway:
            messages.warning(request, "Only 'GANGWAY VISUAL INSPECTION CERTIFICATE according to EN 526:2016' is currently enabled.")
            return redirect('create_report')
    else:
        selected_procedure = procedures.filter(Q(standard_code="EN 526:2016") | Q(title__icontains="gangway")).first() or procedures.first()
    
    if request.method == 'POST':
        procedure_id = request.POST.get('procedure_id')
        procedure = get_object_or_404(InspectionProcedure, id=procedure_id) if procedure_id else selected_procedure
        
        report_number = request.POST.get('report_number', '').strip()
        if not report_number:
            report_number = generate_unique_report_number()
            
        if NDTReport.objects.filter(report_number__iexact=report_number).exists():
            suggested = generate_unique_report_number()
            messages.error(request, f"Certificate number '{report_number}' is already assigned to another certificate! Please enter a unique number.")
            context = {
                'selected_procedure': procedure,
                'procedures': procedures,
                'profile': profile,
                'new_report_number': suggested,
            }
            return render(request, 'report_form.html', context)

        vessel_name = request.POST.get('vessel_name')
        project_no = request.POST.get('project_no')
        make_manufacturer = request.POST.get('make_manufacturer', 'MTQ Products B.V.')
        year_manufactured = request.POST.get('year_manufactured')
        size_length = request.POST.get('size_length')
        marking_tag = request.POST.get('marking_tag')
        inspection_date = request.POST.get('inspection_date')
        validity_until = request.POST.get('validity_until')
        status = request.POST.get('status', 'APPROVED')
        approval_statement = request.POST.get('approval_statement', procedure.default_statement if procedure else '')
        notes = request.POST.get('notes', '')
        signature_type = request.POST.get('signature_type', 'LIVE')
        
        report = NDTReport(
            report_number=report_number,
            procedure=procedure,
            inspector=request.user,
            vessel_name=vessel_name,
            project_no=project_no,
            make_manufacturer=make_manufacturer,
            year_manufactured=year_manufactured,
            size_length=size_length,
            marking_tag=marking_tag,
            inspection_date=inspection_date,
            validity_until=validity_until,
            status=status,
            approval_statement=approval_statement,
            notes=notes,
            signature_type=signature_type,
        )
        
        # Process Signature
        if signature_type == 'LIVE':
            canvas_data = request.POST.get('signature_canvas_data')
            if canvas_data and 'data:image' in canvas_data:
                format_str, imgstr = canvas_data.split(';base64,')
                ext = format_str.split('/')[-1]
                file_name = f"sig_{report_number}_{uuid.uuid4().hex[:4]}.{ext}"
                report.signature_image.save(file_name, ContentFile(base64.b64decode(imgstr)), save=False)
        elif signature_type == 'UPLOADED' and 'signature_file' in request.FILES:
            report.signature_image = request.FILES['signature_file']
        elif signature_type == 'SAVED' and profile.profile_signature:
            report.signature_image = profile.profile_signature
            
        report.save()
        messages.success(request, f"Certificate {report.report_number} created successfully!")
        return redirect('certificate_detail', pk=report.pk)
        
    context = {
        'selected_procedure': selected_procedure,
        'procedures': procedures,
        'profile': profile,
        'new_report_number': generate_unique_report_number(),
    }
    return render(request, 'report_form.html', context)


@login_required
def edit_report(request, pk):
    report = get_object_or_404(NDTReport, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.role != 'ADMIN' and report.inspector != request.user:
        messages.error(request, "You do not have permission to edit this report.")
        return redirect('report_list')
        
    procedures = InspectionProcedure.objects.all()
    selected_procedure = report.procedure or procedures.first()
    
    if request.method == 'POST':
        new_report_number = request.POST.get('report_number', '').strip()
        if new_report_number and new_report_number != report.report_number:
            if NDTReport.objects.filter(report_number__iexact=new_report_number).exclude(pk=report.pk).exists():
                messages.error(request, f"Certificate number '{new_report_number}' is already assigned to another certificate! Please enter a unique number.")
                context = {
                    'report': report,
                    'selected_procedure': selected_procedure,
                    'procedures': procedures,
                    'profile': profile,
                }
                return render(request, 'report_form.html', context)
            report.report_number = new_report_number

        procedure_id = request.POST.get('procedure_id')
        if procedure_id:
            report.procedure = get_object_or_404(InspectionProcedure, id=procedure_id)
            
        report.vessel_name = request.POST.get('vessel_name')
        report.project_no = request.POST.get('project_no')
        report.make_manufacturer = request.POST.get('make_manufacturer', 'MTQ Products B.V.')
        report.year_manufactured = request.POST.get('year_manufactured')
        report.size_length = request.POST.get('size_length')
        report.marking_tag = request.POST.get('marking_tag')
        report.inspection_date = request.POST.get('inspection_date')
        report.validity_until = request.POST.get('validity_until')
        report.status = request.POST.get('status')
        report.approval_statement = request.POST.get('approval_statement')
        report.notes = request.POST.get('notes')
        
        signature_type = request.POST.get('signature_type')
        if signature_type:
            report.signature_type = signature_type
            if signature_type == 'LIVE':
                canvas_data = request.POST.get('signature_canvas_data')
                if canvas_data and 'data:image' in canvas_data:
                    format_str, imgstr = canvas_data.split(';base64,')
                    ext = format_str.split('/')[-1]
                    file_name = f"sig_{report.report_number}_{uuid.uuid4().hex[:4]}.{ext}"
                    report.signature_image.save(file_name, ContentFile(base64.b64decode(imgstr)), save=False)
            elif signature_type == 'UPLOADED' and 'signature_file' in request.FILES:
                report.signature_image = request.FILES['signature_file']
            elif signature_type == 'SAVED' and profile.profile_signature:
                report.signature_image = profile.profile_signature

        report.save()
        messages.success(request, f"Certificate {report.report_number} updated.")
        return redirect('certificate_detail', pk=report.pk)
        
    context = {
        'report': report,
        'selected_procedure': selected_procedure,
        'procedures': procedures,
        'profile': profile,
    }

    return render(request, 'report_form.html', context)

@login_required
def delete_report(request, pk):
    report = get_object_or_404(NDTReport, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.role != 'ADMIN' and report.inspector != request.user:
        messages.error(request, "You do not have permission to delete this report.")
        return redirect('report_list')
        
    if request.method == 'POST':
        num = report.report_number
        report.delete()
        messages.success(request, f"Report {num} deleted.")
        return redirect('report_list')
        
    return render(request, 'confirm_delete.html', {'object': report, 'type': 'Report'})

@login_required
def certificate_view(request, pk):
    report = get_object_or_404(NDTReport.objects.select_related('inspector', 'procedure'), pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'report': report,
        'profile': profile,
    }
    return render(request, 'certificate.html', context)

@login_required
def procedure_list(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    procedures = InspectionProcedure.objects.all()
    return render(request, 'procedure_list.html', {'procedures': procedures, 'profile': profile})

@login_required
def create_procedure(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role != 'ADMIN':
        messages.error(request, "Only Supervisors/Admins can create procedures.")
        return redirect('procedure_list')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        standard_code = request.POST.get('standard_code')
        description = request.POST.get('description', '')
        default_statement = request.POST.get('default_statement', '')
        
        proc = InspectionProcedure.objects.create(
            title=title,
            standard_code=standard_code,
            description=description,
            default_statement=default_statement,
        )
        messages.success(request, f"Procedure {proc.title} created.")
        return redirect('procedure_list')
        
    return render(request, 'procedure_form.html', {'profile': profile})

@login_required
def edit_procedure(request, pk):
    proc = get_object_or_404(InspectionProcedure, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role != 'ADMIN':
        messages.error(request, "Only Supervisors/Admins can edit procedures.")
        return redirect('procedure_list')
        
    if request.method == 'POST':
        proc.title = request.POST.get('title')
        proc.standard_code = request.POST.get('standard_code')
        proc.description = request.POST.get('description', '')
        proc.default_statement = request.POST.get('default_statement', '')
        proc.save()
        messages.success(request, f"Procedure {proc.title} updated.")
        return redirect('procedure_list')
        
    return render(request, 'procedure_form.html', {'procedure': proc, 'profile': profile})

@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        profile.qualification = request.POST.get('qualification', '')
        profile.certification_no = request.POST.get('certification_no', '')
        profile.company_name = request.POST.get('company_name', '')
        
        if 'profile_signature' in request.FILES:
            profile.profile_signature = request.FILES['profile_signature']
            
        profile.save()
        messages.success(request, "Your profile and signature settings have been updated.")
        return redirect('profile')
        
    return render(request, 'profile.html', {'profile': profile})
