
import pyotp, ssl, certifi,json,hashlib

#django library
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse,HttpResponse
from django.utils import timezone
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.urls import reverse
import uuid


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count

import logging

from django.utils import timezone


#imports models
from django.contrib.admin.models import LogEntry
from webinar.models import Webinar,WebinarAttendees
from exam_portal.models import CertificateTemplate
from exam_portal.serializer import CertificateSerilize
from django.contrib.auth.models import User
from .models import UserProfile, TrustedDevice,Otp,PasswordReset


#decorator
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .email_service import send_email
from datetime import timedelta


# Create your views here.


#decorator
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url="login")(view_func)


def user_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and not u.is_staff)(view_func)



#redirect upon errors
def csrf_failure(request, reason=""):
    messages.error(request, "Your session expired. Please log in again.")
    return redirect("login") 


def custom_page_not_found(request, exception):
    messages.error(request, "The page you were looking for was not found.You will redirected to this page.")
    return redirect("index") 


def handle_error(request, exception=None):
    messages.warning(request, "Something went wrong. Redirected to homepage.")
    return redirect("index")


#hash
def create_device_hash(request):
    x_forward=request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forward:
        user_ip = x_forward.split(',')[0].strip()
    else:
        user_ip=request.META.get("REMOTE_ADDR")

    user_agent=request.META.get("HTTP_USER_AGENT")

    combined=f"{user_ip}_{user_agent}"
    binary_combined=combined.encode()
    hash=hashlib.sha256(binary_combined).hexdigest()

    return hash


#login handler
def index(request):
    webinar=Webinar.objects.all()
    upcoming_webinars = Webinar.objects.filter(
        start_date__gte=timezone.now()  
    ).order_by('start_date')[:3]

    print(settings.EMAIL_HOST_USER)
    print(settings.EMAIL_HOST)

    if request.user.is_authenticated:
        
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_events')
        else:
            return redirect('user_dashboard')

    return render(request, 'login/index.html',{
        'webinars':upcoming_webinars
    })


def logout_view(request):
    logout(request)
    return redirect("index")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        
        try:
            from django.contrib.auth.models import User
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user:
            request.session['user_id'] = user.id
            
            # Check if device is trusted
            hash = create_device_hash(request)
            if TrustedDevice.objects.filter(user=user, hash=hash).exists():
                login(request, user)
                return redirect("index")
            else:
                request.session['hash'] = hash
                return redirect('otp', user_id=user.id)
        else:
            return render(request, 'login/login.html', {"credential_error": "Invalid Email or Password"})
    
    return render(request, 'login/login.html')
def generate_otp(request, user_id=None):
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    
    # Check for existing OTP record
    current_otp = Otp.objects.filter(user=user).first()
    
    # Check if user is locked out
    if current_otp and current_otp.is_locked_out():
        remaining_seconds = current_otp.get_lockout_remaining_seconds()
        remaining_minutes = remaining_seconds // 60
        
        return render(request, 'login/otp.html', {
            'locked_out': True,
            'error': f'Account locked due to too many failed attempts. Try again in {remaining_minutes} minutes.',
            'user': user,
            'user_id': user_id
        })
    
    # Clear expired lockout
    if current_otp and current_otp.lockout_until and not current_otp.is_locked_out():
        current_otp.clear_lockout()
   
    # Handle OTP verification (POST request)
    if request.method == 'POST':
        user_otp = (request.POST.get('otp') or '').strip()
        
        if not current_otp:
            return render(request, 'login/otp.html', {
                'error': 'OTP not found. Please try again.',
                'user_id': user_id,
                'expired': True
            })
        
        # Check if OTP is expired
        time_diff = timezone.now() - current_otp.created_at
        if time_diff.total_seconds() > 300:  
            current_otp.is_valid = False
            current_otp.save()
            
            return render(request, 'login/otp.html', {
                'error': 'OTP has expired. Please request a new one.',
                'user_id': user_id,
                'expired': True
            })
        
        
        totp = pyotp.TOTP(current_otp.secret_key, interval=300)
        
        
        print(f"User entered OTP: {user_otp}")
        print(f"Current valid OTP: {totp.now()}")
        print(f"Secret key: {current_otp.secret_key}")
        print(f"Time diff: {time_diff.total_seconds()} seconds")
        
        
        is_valid = False
        
        
        if totp.verify(user_otp, valid_window=1):  
            is_valid = True
            print("OTP verified with method 1 (direct verification)")
        
    
        if not is_valid:
            current_time = timezone.now().timestamp()
            current_otp_code = totp.at(current_time)
            if user_otp == current_otp_code:
                is_valid = True
                print("OTP verified with method 2 (manual time)")
        

        if not is_valid and hasattr(current_otp, 'otp') and current_otp.otp:
            if user_otp == str(current_otp.otp):
                is_valid = True
                print("OTP verified with method 3 (stored OTP)")
        
        if is_valid:
            # Successful login - clear everything
            login(request, user)
            request.session.modified = True
            request.session.pop('username', None)
            
            # Clear OTP generation flag
            session_key = f"otp_generated_{user_id}"
            request.session.pop(session_key, None)
            
            print('The OTP is correct')
            
            # Handle trusted device
            device_hash = request.session.get('hash')
            if device_hash:
                TrustedDevice.objects.get_or_create(
                    user=user,
                    hash=device_hash
                )
                request.session.pop('hash', None)

            current_otp.delete()
            return redirect('index')
        else:
            # Wrong OTP - increment counters
            current_otp.retry += 1
            current_otp.total_failed_attempts += 1
            current_otp.last_attempt = timezone.now()
            current_otp.save()
            
            print(f"OTP verification failed. Retry: {current_otp.retry}, Total failed: {current_otp.total_failed_attempts}")
            
            if request.user.is_authenticated:
                return redirect('index')
            
            # Check if we've reached 10 total failed attempts
            if current_otp.total_failed_attempts >= 10:
                # Lock out for 10 minutes
                current_otp.lockout_until = timezone.now() + timedelta(minutes=10)
                current_otp.is_valid = False
                current_otp.save()
                
                return render(request, 'login/otp.html', {
                    'locked_out': True,
                    'error': 'Account locked due to too many failed attempts. Try again in 10 minutes.',
                    'user': user,
                    'user_id': user_id
                })
            
            # Check if current OTP has 3 attempts (generate new OTP)
            if current_otp.retry >= 3:
                current_otp.is_valid = False
                current_otp.save()
                session_key = f"otp_generated_{user_id}"
                request.session.pop(session_key, None)
                return render(request, 'login/otp.html', {
                    'error': f'Too many failed attempts for current OTP. Please request a new OTP. (Total attempts: {current_otp.total_failed_attempts}/10)',
                    'user_id': user_id,
                    'expired': True
                })
            
            # Show remaining attempts for current OTP and total attempts
            return render(request, 'login/otp.html', {
                'error': f'Invalid OTP. {3 - current_otp.retry} attempts remaining for current OTP. (Total attempts: {current_otp.total_failed_attempts}/10)',
                'user_id': user_id
            })

    # Handle OTP generation (GET request)
    existing_otp = Otp.objects.filter(user=user).first()
    should_generate_otp = False
    
    if existing_otp:
        time_diff = timezone.now() - existing_otp.created_at
        is_expired = time_diff.total_seconds() > 300
        
        if is_expired:
            existing_otp.is_valid = False
            existing_otp.save()
            
            return render(request, 'login/otp.html', {
                'error': 'OTP has expired. Please request a new one.',
                'user_id': user_id,
                'expired': True
            })
        elif existing_otp.is_valid:
            should_generate_otp = False
        else:
            should_generate_otp = True
    else:
        should_generate_otp = True
   
    if should_generate_otp:
        session_key = f"otp_generated_{user_id}"
        
        if not request.session.get(session_key):
            # Generate new OTP with better time synchronization
            otp_secret_key = pyotp.random_base32()
            totp = pyotp.TOTP(otp_secret_key, interval=300)
            
            # Use current timestamp for consistent OTP generation
            current_time = timezone.now()
            otp_code = totp.at(current_time.timestamp())
            
            print(f"Generated OTP: {otp_code} at time: {current_time}")
            print(f"Secret key: {otp_secret_key}")
            
            if existing_otp:
                # Update existing OTP record but keep total_failed_attempts
                existing_otp.otp = otp_code
                existing_otp.secret_key = otp_secret_key
                existing_otp.created_at = current_time
                existing_otp.retry = 0  # Reset current OTP attempts
                existing_otp.is_valid = True
                existing_otp.last_attempt = None 
                # Keep total_failed_attempts unchanged
                existing_otp.save()
            else:
                # Create new OTP record
                Otp.objects.create(
                    user=user,
                    otp=otp_code,
                    secret_key=otp_secret_key,
                    created_at=current_time,
                    retry=0,
                    is_valid=True,
                    total_failed_attempts=0  # Start fresh for new users
                )

            # Send OTP email
            print(f"This is the OTP code: {otp_code}")
            result = send_email(
                to_email=user.email,
                subject="OTP code From SDO",
                body=f'Enter this code to confirm your login: {otp_code}\n\nThis code will expire in 5 minutes.'
            )
        
            # Mark OTP as generated in session
            request.session[session_key] = True
    
    return render(request, 'login/otp.html', {
        'user_id': user_id
    })


def resend_otp(request, user_id):
    """
    Handle explicit resend OTP requests
    Generates new OTP and sends email immediately
    """
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    existing_otp = Otp.objects.filter(user=user).first()
    
    if existing_otp and existing_otp.is_locked_out():
        return redirect('otp', user_id=user_id)
    
    # Generate new OTP with proper time synchronization
    otp_secret_key = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret_key, interval=300)
    
    current_time = timezone.now()
    otp_code = totp.at(current_time.timestamp())
    
    print(f"Resending OTP code: {otp_code} at time: {current_time}")
    print(f"Secret key: {otp_secret_key}")
    
    if existing_otp:
        existing_otp.otp = otp_code
        existing_otp.secret_key = otp_secret_key
        existing_otp.created_at = current_time
        existing_otp.retry = 0  
        existing_otp.is_valid = True
        existing_otp.last_attempt = None
        existing_otp.save()
    else:
        # Create new OTP record if none exists
        Otp.objects.create(
            user=user,
            otp=otp_code,
            secret_key=otp_secret_key,
            created_at=current_time,
            retry=0,
            is_valid=True,
            total_failed_attempts=0
        )
    
    # Send OTP email
    result = send_email(
        to_email=user.email,
        subject="OTP code From SDO - Resent",
        body=f'Enter this code to confirm your login: {otp_code}\n\nThis code will expire in 5 minutes.'
    )
    
    # Clear and reset the session flag
    session_key = f"otp_generated_{user_id}"
    request.session[session_key] = True
    
    # Redirect back to OTP page
    return redirect('otp', user_id=user_id)

#user views
@user_required
def user_dashboard(request):
    today = timezone.localtime().date()
    upcoming_webinar=WebinarAttendees.objects.filter(user=request.user  , webinar__start_date__gte=today)   
    past_webinar=WebinarAttendees.objects.filter(user=request.user, webinar__start_date__lt=today )
    upcoming_messages=""
    history_messages=""

    if not upcoming_webinar.exists():
        upcoming_messages="No webinar asssigned to you please wait for further notice"
    
    if not past_webinar.exists():
        history_messages="No Webinar Currently"


    return render(request, "login/user_nav/user_dashboard.html",{
        "upcoming_webinars":upcoming_webinar,
        "past_webinars":past_webinar,
        "upcoming_message":upcoming_messages,
        "past_message":history_messages
    })

@user_required
def calendar(request):
    today=timezone.now().date()
    upcoming_webinar=WebinarAttendees.objects.filter(user=request.user, webinar__start_date__gte=today ) 
    

    return render(request,"login/user_nav/calendar.html",{
        'upcoming_webinars':upcoming_webinar
    })

def event_data(request):
    data=[]
    webinars=Webinar.objects.all()
    for webinar in webinars:
        data.append({
            "title":webinar.title,
            "start":webinar.start_date.isoformat()
        })

    return JsonResponse(data, safe=False)

@user_required
def user_setting(request):
    return render(request, "login/user_nav/user_setting.html")

@user_required
def certificate(request):
    today = timezone.now().date()

    ongoing_webinars = Webinar.objects.filter(
        until_date__gt=today,
        attendees__user=request.user
    )
    completed_webinars = Webinar.objects.filter(
        until_date__lt=today,
        attendees__user=request.user
    )




    
    return render(request, 'login/user_nav/certificate.html', {
        'ongoing_webinars':ongoing_webinars,
        'completed_webinars': completed_webinars,

    })


def certificate_data(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    certificate = CertificateTemplate.objects.filter(webinar=webinar)
    data = CertificateSerilize(certificate, many=True).data
    return JsonResponse(data, safe=False)


#admin views
@admin_required
def admin_calendar(request):
    today=timezone.now().date()
    upcoming_webinars=Webinar.objects.filter(start_date__gte=today ) 
    print(upcoming_webinars)
    return render(request,"login/admin_panel/calendar.html",{
       
        "upcoming_webinars":upcoming_webinars
    })

@admin_required
def admin_certificate(request):
    webinars=Webinar.objects.all()
    today=timezone.now().date()
    
    return render(request, "login/admin_panel/certificate.html",{
        'webinars':webinars,
        'today':today
    })


@admin_required
def admin_events(request):
    webinar=Webinar.objects.all().order_by("-id")

    return render(request, "login/admin_panel/events.html",{
        'webinars':webinar,
      
    })

@admin_required
def admin_setting(request):
    return render(request, "login/admin_panel/setting.html")


@admin_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
 
    return render(request, 'login/admin_panel/users.html', {
        'all_users': users  
    })

#create user and edit credential
@admin_required
def register_user(request):
    if request.method=="POST":

        first_name=request.POST.get("user_firstname")
        last_name=request.POST.get("user_lastname")
        birth_date=request.POST.get("user_birth_date")


        email=request.POST.get("user_email")
        password=request.POST.get("user_passwogitrd")
        deped_id=request.POST.get("deped_id")
        username=deped_id

        if User.objects.filter(username=username).exists():
            messages.error(request,"username Already Exist")
            return redirect('admin_users')
            
        elif User.objects.filter(email=email).exists():
            messages.error(request,"Email Already Exist")
            return redirect('admin_users')
        else:
            user= User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
            profile=UserProfile.objects.create(user=user, deped_id=deped_id, birthday=birth_date)


        result = send_email(
        to_email=f"{user.email}",
        subject="Welcome! Your Account Has Been Created",
        body=f"""
            Hi {user.first_name},

            We're happy to let you know that your account has been successfully created by our team.

            You can now log in and start exploring the system:
            🔐 Email: {user.email}
                username:{user.username}
                first name: {user.first_name}
                last name: {user.last_name}
                deped id:{profile.deped_id}
            🔑 Temporary Password: {user.password}

            If have any questions, feel free to contact us.

            Welcome aboard!

            Best regards,  
            The A"""
        )
        messages.success(request,"Successfully registered")
        return redirect('admin_users')
    return redirect('admin_users')

@admin_required
def generete_authorization_key(request):
   
    otp=pyotp.random_base32()
    code=pyotp.TOTP(otp).now()
    request.session['authorization_key']=code

    send_email(
        #check -problem
        to_email=f'{settings.EMAIL_HOST_USER}',
        subject="Request for Admin Authorization Code",
        body= f'Staff {request.user} has requested to create an admin account. If you approve this request, please share the following authorization code: {code}'
    )
    return redirect('admin_users')
            
@admin_required
def create_admin(request):
    if request.method == 'POST':
 
        first_name=request.POST.get("staff_firstname")
        last_name=request.POST.get("staff_lastname")
        deped_id=request.POST.get("staff_deped_id")
        email = request.POST.get("staff_email")
        password = request.POST.get("staff_password")
        birthday= request.POST.get("staff_birth_date")
        username = deped_id

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password)
            user.is_staff = True
            user.save()
            UserProfile.objects.create(user=user,deped_id=deped_id, birthday=birthday)
            messages.success(request, "Admin account created successfully.")

    return redirect('admin_users')


@admin_required
def delete_user(request, id):
    user=User.objects.filter(id=id)
    user.delete()

    return redirect("admin_users")

@login_required
def edit_user(request):
    user = User.objects.get(id=request.user.id)
    profile = UserProfile.objects.get(user=user)
    user_taken="username already taken"

    redirection=["admin_panel/setting.html","user_nav/user_setting.html"]
    redirected=""

    if request.method == 'POST':
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
            
        user.first_name = first_name
        user.last_name = last_name

        username=request.POST.get('username')
        if username:
            if User.objects.filter(username=username):
                if request.user.is_superuser or request.user.is_staff:
                    redirected=redirection[0]
                else:
                    redirected=redirection[1]
                return render(request, f"login/{redirected}",{
                    "user_taken":user_taken
                })
            user.username=username

        
        email = request.POST.get("email")
        img = request.FILES.get("img")  
        number = request.POST.get('number')
        school = request.POST.get('school')

        if email:
            user.email = email

        user.save()

        if img:
            profile.img = img
        if number:
            profile.number = number
        if school:
            profile.school = school
        profile.save()

        messages.success(request,"Profile Successfully Applied Changes")

    if request.user.is_superuser or request.user.is_staff:
        return redirect("admin_setting")
    else:
        return redirect("user_setting")



@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
    
        errors = []
        
        
        if not authenticate(username=request.user.username, password=current_password):
            errors.append("Current password is incorrect")
        

        if len(new_password) < 8:
            errors.append("New password must be at least 8 characters long")
        
    
        if new_password != confirm_password:
            errors.append("New password and confirmation password do not match")
        

        if authenticate(username=request.user.username, password=new_password):
            errors.append("New password must be different from current password")
        
        if not errors:
  
            user = request.user
            user.set_password(new_password)
            user.save()
            
            update_session_auth_hash(request, user)
            
            messages.success(request, "Password changed successfully!")
        else:
            for error in errors:
                messages.error(request, error)
            
        
            redirected = "admin_panel/setting.html" if (request.user.is_superuser or request.user.is_staff) else "user_nav/user_setting.html"
            return render(request, f"login/{redirected}", {
                "error_password": errors[0] if errors else None
            })
  
    if request.user.is_superuser or request.user.is_staff:
        return redirect("admin_setting")
    else:
        return redirect("user_setting")
    
@admin_required
def log_list(request):
 
    logs = LogEntry.objects.filter(
        user__is_staff=True
    ).select_related('user').order_by('-action_time')
    users = User.objects.select_related('user_profile').order_by('-last_login')


    
    context = {
        'logs': logs,
        'users': users,
    }
    
    return render(request, "login/admin_panel/admin_log.html", context)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
            
           
            PasswordReset.objects.filter(user=user, used=False).delete()
            
        
            reset_token = PasswordReset.objects.create(user=user)
            
        
            reset_link = request.build_absolute_uri(
                reverse('reset_password', args=[reset_token.token])
            )
            
         
            send_email(
                to_email=email,
                subject="Password Reset - SDO",
                body=f"""
                Hello {user.first_name or user.username},
                
                You requested a password reset. Click the link below to reset your password:
        
                {reset_link}
    
                This link will expire in 1 hour.

                If you didn't request this, ignore this email.
                """
            )
            
            messages.success(request, 'Password reset link sent to your email!')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.success(request, 'If that email exists, a reset link has been sent.')
            return redirect('login')
    
    return render(request, 'login/forgot_password.html')


def reset_password(request, token):
    try:
        reset_obj = PasswordReset.objects.get(token=token, used=False)
        
        if reset_obj.is_expired():
            messages.error(request, 'Reset link has expired. Please request a new one.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'login/reset_password.html', {'token': token})
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'login/reset_password.html', {'token': token})
            
            # Reset password
            user = reset_obj.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_obj.used = True
            reset_obj.save()
            
            messages.success(request, 'Password reset successfully! You can now login.')
            return redirect('login')
        
        return render(request, 'login/reset_password.html', {'token': token})
        
    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('forgot_password')


def cal_event_data(request, id):
    webinar = get_object_or_404(Webinar, id=id)

    categories = {
        "speaker": [],
        "venue": [],
        "meals": [],
        "manage": []
    }

    for evaluation in webinar.evaluation.all():
        total = [evaluation.q1, evaluation.q2, evaluation.q3, evaluation.q4, evaluation.q5, evaluation.q6]
        valid_numbers = [s for s in total if s is not None]
        average = sum(valid_numbers) / len(valid_numbers) if valid_numbers else 0
        average = round(average, 2) 

        if evaluation.type in categories:
            categories[evaluation.type].append(average)

    results = {}
    for key, values in categories.items():
        if values:
            results[key] = round(sum(values) / len(values), 2)
        else:
            results[key] = 0


    all_values = categories["speaker"] + categories["venue"] + categories["meals"] + categories["manage"]
    results["overall"] = round(sum(all_values) / len(all_values), 2) if all_values else 0

    return JsonResponse(results)



logger = logging.getLogger(__name__)

@login_required
def get_completed_events(request):
    """
    Get list of completed events with basic info for comparison dropdown.
    Only returns events that have evaluations and are past their until_date.
    """
    try:
        now = timezone.now().date()  # use date since until_date is a DateField

        completed_webinars = Webinar.objects.filter(
            until_date__lt=now,          # must be completed
            evaluation__isnull=False     # has at least one evaluation
        ).annotate(
            response_count=Count('evaluation', distinct=True)
        ).filter(
            response_count__gt=0
        ).distinct().order_by('-start_date')

        events_data = [
            {
                'id': webinar.id,
                'title': webinar.title,
                'date': webinar.start_date.strftime('%B %d, %Y') if webinar.start_date else 'No date',
                'response_count': webinar.response_count
            }
            for webinar in completed_webinars
        ]

        return JsonResponse(events_data, safe=False)

    except Exception as e:
        logger.error(f"Error fetching completed events: {str(e)}")
        return JsonResponse({'error': 'Failed to fetch completed events'}, status=500)

    

@login_required 
@require_http_methods(["GET"])
def compare_events(request):
    """
    Compare ratings between two events and return comparison data.
    Expected URL parameters: event1, event2
    """
    event1_id = request.GET.get('event1')
    event2_id = request.GET.get('event2')

    if not event1_id or not event2_id:
        return JsonResponse({'error': 'Both event1 and event2 parameters are required'}, status=400)

    if event1_id == event2_id:
        return JsonResponse({'error': 'Cannot compare an event with itself'}, status=400)

    try:
        # Fetch webinars
        event1 = get_object_or_404(Webinar, id=event1_id)
        event2 = get_object_or_404(Webinar, id=event2_id)
        print(f"hello {event1}")
        print(f"hello {event2}")

        # Get evaluation data
        event1_data = calculate_event_ratings(event1)
        event2_data = calculate_event_ratings(event2)

        comparison_data = {
            'event1': {
                'id': event1.id,
                'title': event1.title,
                'date': event1.start_date.strftime('%B %d, %Y') if event1.start_date else 'No date',
                'ratings': event1_data.get('question_averages', {}),
                'categories': event1_data.get('categories', []),
                'overall': event1_data.get('overall', 0),
                'total_responses': event1_data.get('total_responses', 0),
            },
            'event2': {
                'id': event2.id,
                'title': event2.title,
                'date': event2.start_date.strftime('%B %d, %Y') if event2.start_date else 'No date',
                'ratings': event2_data.get('question_averages', {}),
                'categories': event2_data.get('categories', []),
                'overall': event2_data.get('overall', 0),
                'total_responses': event2_data.get('total_responses', 0),
            }
        }

        return JsonResponse(comparison_data, safe=False)

    except Exception as e:
        logger.error(f"Error comparing events ({event1_id}, {event2_id}): {str(e)}")
        return JsonResponse({'error': 'Failed to compare events'}, status=500)


def calculate_event_ratings(webinar):
  
    evaluations = webinar.evaluation.all()
    
    if not evaluations.exists():
        return {
            'question_averages': [0, 0, 0, 0, 0, 0],
            'categories': {'speaker': 0, 'venue': 0, 'meals': 0, 'manage': 0},
            'overall': 0,
            'total_responses': 0
        }

    # Initialize data structures
    question_totals = {'q1': [], 'q2': [], 'q3': [], 'q4': [], 'q5': [], 'q6': []}
    categories = {'speaker': [], 'venue': [], 'meals': [], 'manage': []}

    for evaluation in evaluations:
        # Collect question scores
        questions = {
            'q1': evaluation.q1, 'q2': evaluation.q2, 'q3': evaluation.q3,
            'q4': evaluation.q4, 'q5': evaluation.q5, 'q6': evaluation.q6
        }
        
        # Add valid scores to question totals
        for question, score in questions.items():
            if score is not None:
                question_totals[question].append(score)
        
        # Calculate evaluation average for category grouping
        valid_scores = [score for score in questions.values() if score is not None]
        if valid_scores:
            eval_avg = sum(valid_scores) / len(valid_scores)
            eval_type = getattr(evaluation, 'type', None)
            if eval_type and eval_type in categories:
                categories[eval_type].append(eval_avg)

    # Calculate question averages (for chart display)
    question_averages = []
    for question in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6']:
        scores = question_totals[question]
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        question_averages.append(avg)

    # Calculate category averages
    category_averages = {}
    for category, values in categories.items():
        category_averages[category] = round(sum(values) / len(values), 2) if values else 0

    # Calculate overall average
    all_scores = []
    for scores in question_totals.values():
        all_scores.extend(scores)
    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

    return {
        'question_averages': question_averages,
        'categories': category_averages,
        'overall': overall_avg,
        'total_responses': evaluations.count()
    }


@login_required
@require_http_methods(["GET"])
def get_event_details(request, event_id):

    try:
        webinar = get_object_or_404(Webinar, id=event_id)
        evaluation_count = webinar.evaluation.count()
        
        event_data = {
            'id': webinar.id,
            'title': webinar.title,
            'description': webinar.description,
            'date': webinar.start_date.strftime('%B %d, %Y') if webinar.start_date else 'No date',
            'time': webinar.time.strftime('%I:%M %p') if hasattr(webinar, 'time') and webinar.time else 'No time',
            'response_count': evaluation_count,
            'status': 'completed' if evaluation_count > 0 else 'no_responses'
        }
        
        return JsonResponse(event_data)
        
    except Webinar.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching event details for {event_id}: {str(e)}")
        return JsonResponse({'error': 'Failed to fetch event details'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_event_statistics(request, event_id):
    """
    Get comprehensive statistics for an event including response rates,
    rating distributions, etc.
    """
    try:
        webinar = get_object_or_404(Webinar, id=event_id)
        evaluations = webinar.evaluation.all()
        
        if not evaluations.exists():
            return JsonResponse({
                'event_title': webinar.title,
                'total_responses': 0,
                'statistics': None
            })

        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        question_stats = {}
        
        for question in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6']:
            question_stats[question] = {
                'average': 0,
                'responses': 0,
                'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        for evaluation in evaluations:
            questions = [evaluation.q1, evaluation.q2, evaluation.q3, 
                        evaluation.q4, evaluation.q5, evaluation.q6]
            
            for i, score in enumerate(questions, 1):
                if score is not None:
                    question_key = f'q{i}'
                    question_stats[question_key]['responses'] += 1
                    question_stats[question_key]['distribution'][score] += 1
                    rating_distribution[score] += 1

        # Calculate averages
        for question_key in question_stats:
            stats = question_stats[question_key]
            if stats['responses'] > 0:
                total_score = sum(rating * count for rating, count in stats['distribution'].items())
                stats['average'] = round(total_score / stats['responses'], 2)

        return JsonResponse({
            'event_title': webinar.title,
            'total_responses': evaluations.count(),
            'overall_rating_distribution': rating_distribution,
            'question_statistics': question_stats,
            'statistics': calculate_event_ratings(webinar)
        })

    except Exception as e:
        logger.error(f"Error fetching event statistics for {event_id}: {str(e)}")
        return JsonResponse({'error': 'Failed to fetch event statistics'}, status=500)
    

