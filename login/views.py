
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
    
    credential_error = ""
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            request.session['user_id'] = user.id
            print(f"This username on login view {username}")
            
            hash = create_device_hash(request)
            device = TrustedDevice.objects.filter(user=user, hash=hash).first()
            
            if device:
                login(request, user)
                return redirect("index")
            else:
                request.session['hash'] = hash
                return redirect('otp', user_id=user.id)
        else:
            credential_error = "Invalid Username or Password"
    
    return render(request, 'login/login.html', {"credential_error": credential_error})


def generate_otp(request, user_id=None):
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    otp_code = None 
    
   
    if request.method == 'POST':
        user_otp = (request.POST.get('otp') or '').strip()
        
        current_otp = Otp.objects.filter(user=user).first()
        if current_otp:
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
            
            if totp.verify(user_otp):
              
                login(request, user)
                request.session.modified = True
                request.session.pop('username', None)
                request.session.pop("otp_generated", None)
                print('the otp is correct')
                
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
       
                current_otp.retry += 1
                current_otp.last_attempt = timezone.now()
                current_otp.save()
                
                if request.user.is_authenticated:
                    return redirect('index')
                
                if current_otp.retry >= 3:
           
                    current_otp.is_valid = False
                    current_otp.save()
                    current_otp.delete()
                    request.session.pop("otp_generated", None)
                    return render(request, 'login/otp.html', {
                        'error': 'Too many failed attempts. Please request a new OTP.',
                        'user_id': user_id,
                        'expired': True
                    })
                
             
                return render(request, 'login/otp.html', {
                    'error': f'Invalid OTP. {3 - current_otp.retry} attempts remaining.',
                    'user_id': user_id
                })
        else:
            return render(request, 'login/otp.html', {
                'error': 'OTP not found. Please try again.',
                'user_id': user_id,
                'expired': True
            })

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
            if existing_otp:
           
                otp_secret_key = pyotp.random_base32()
                totp = pyotp.TOTP(otp_secret_key, interval=300)
                otp_code = totp.now()
                
                existing_otp.otp = otp_code
                existing_otp.secret_key = otp_secret_key
                existing_otp.created_at = timezone.now()
                existing_otp.retry = 0
                existing_otp.is_valid = True
                existing_otp.last_attempt = None 
                existing_otp.save()
            else:
            
                otp_secret_key = pyotp.random_base32()
                totp = pyotp.TOTP(otp_secret_key, interval=300)
                otp_code = totp.now()
                
                otp = Otp.objects.create(
                    user=user,
                    otp=otp_code,
                    secret_key=otp_secret_key,
                    created_at=timezone.now(),
                    retry=0,
                    is_valid=True  
                )


    if otp_code:
        print(f"this is the otp code: {otp_code}")
        result = send_email(
            to_email=f"{user.email}",
            subject="OTP code From SDO",
            body=f'Enter this code to confirm your login: {otp_code}\n\nThis code will expire in 5 minutes.'
        )
    
        session_key = f"otp_generated_{user_id}"
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
    
    # Find existing OTP record
    existing_otp = Otp.objects.filter(user=user).first()
    
    if existing_otp:
        # Update existing OTP record with new values
        otp_secret_key = pyotp.random_base32()
        totp = pyotp.TOTP(otp_secret_key, interval=300)
        otp_code = totp.now()
        
        existing_otp.otp = otp_code
        existing_otp.secret_key = otp_secret_key
        existing_otp.created_at = timezone.now()
        existing_otp.retry = 0
        existing_otp.is_valid = True
        existing_otp.last_attempt = None
        existing_otp.save()
    else:
        # Create new OTP record if none exists
        otp_secret_key = pyotp.random_base32()
        totp = pyotp.TOTP(otp_secret_key, interval=300)
        otp_code = totp.now()
        
        existing_otp = Otp.objects.create(
            user=user,
            otp=otp_code,
            secret_key=otp_secret_key,
            created_at=timezone.now(),
            retry=0,
            is_valid=True
        )
    
    # Send OTP email
    print(f"Resending OTP code: {otp_code}")
    result = send_email(
        to_email=f"{user.email}",
        subject="OTP code From SDO - Resent",
        body=f'Enter this code to confirm your login: {otp_code}\n\nThis code will expire in 5 minutes.'
    )
    
    # Clear the session flag to ensure proper state
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
    print("hello")
    print(today)
    test=WebinarAttendees.objects.get(id=1)
    print(test.user)
    print(request.user.id)
    print(f"UPCOMING: {upcoming_webinar} , PAST: {past_webinar}")
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
    webinar=Webinar.objects.all()
    return render(request, "login/admin_panel/events.html",{
        'webinars':webinar,
      
    })

@admin_required
def admin_setting(request):
    return render(request, "login/admin_panel/setting.html")

@admin_required
def admin_users(request):
    users = User.objects.all()  # Get all users
    return render(request, 'login/admin_panel/users.html', {
        'all_users': users  
    })

#create user and edit credential
@admin_required
def register_user(request):
    if request.method=="POST":

        first_name=request.POST.get("user_firstname")
        last_name=request.POST.get("user_lastname")
        birth_date=request.POST.get("birth_date")


        email=request.POST.get("user_email")
        password=request.POST.get("user_password")
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
            profile=UserProfile.objects.create(user=user, deped_id=deped_id, birth_date=birth_date)


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
        password = request.POST.get("admin_password")
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
        full_name = request.POST.get('fullname', '').strip()
        if full_name:
            name = full_name.split(" ")
            if not name:
                first_name = ''
                last_name = ''
            elif len(name) == 1:
                first_name = name[0]
                last_name = ''
            else:
                first_name = name[0]
                last_name = ' '.join(name[1:])

            
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

    if request.user.is_superuser or request.user.is_staff:
        return redirect("admin_setting")
    else:
        return redirect("user_setting")


@login_required
def change_password(request):
    user = request.user

    redirection=["admin_panel/setting.html","user_nav/user_setting.html"]
    redirected=""

    if request.method == 'POST':
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        
        if current_password and new_password:

            if user.check_password(current_password):
                print("that password is check")
                user.set_password(new_password)
                user.save()

                update_session_auth_hash(request, user)

                if user.is_superuser or user.is_staff:

                    return redirect("admin_setting")
                else:
                    return redirect("user_setting")
            else:
                if request.user.is_staff or request.user.is_superuser:
                    redirected=redirection[0]
                else:
                    redirected=redirection[1]

                return render(request, f'login/{redirected}', {
                    'error_password': 'Current password is incorrect.'
                })

@admin_required
def log_list(request):
    logs = LogEntry.objects.filter(user__is_staff=True).order_by('-action_time')
    return render(request, "login/admin_panel/admin_log.html", {"logs": logs})


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

