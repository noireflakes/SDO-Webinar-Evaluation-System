from django.shortcuts import render,redirect,get_object_or_404
from .models import UserProfile
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail,EmailMessage
from django.contrib import messages
import pyotp
from django.http import JsonResponse,HttpResponse
from django.utils import timezone
from django.core import serializers
from webinar.models import Webinar,WebinarAttendees
from exam_portal.models import CertificateTemplate
from exam_portal.serializer import CertificateSerilize
import json
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
# Create your views here.

#login handler
def index(request):
    webinar=Webinar.objects.all()
    upcoming_webinars = Webinar.objects.filter(
        start_date__gte=timezone.now()  
    ).order_by('start_date')[:3]

    if request.user.is_authenticated:
        
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_events')
        else:
            return redirect('user_dashboard')

    return render(request, 'login/index.html',{
        'webinars':upcoming_webinars
    })

def login_view(request):
    credential_error=""
    if request.method=="POST":

        if request.user.is_authenticated:
            return render(request, 'login/login.html',{"credential_error":"Sign out your other account before signing in"})

        username=request.POST.get("username")
        password=request.POST.get("password")

        user=authenticate(username=username,password=password)

        if user is not None:
            request.session['username']=username
        
            return redirect(generate_otp)
        else:
            credential_error="Invalid Username or Password"
        
    return render(request, 'login/login.html',{"credential_error":credential_error})

def logout_view(request):
    logout(request)
    return redirect("index")

def generate_otp(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')

    user = get_object_or_404(User, username=username)

    if 'otp_secret_key' not in request.session:
        request.session['otp_secret_key'] = pyotp.random_base32()

    otp_secret_key = request.session['otp_secret_key']

   
    totp = pyotp.TOTP(otp_secret_key, interval=300)
    otp_code = totp.now()

    if request.method == 'POST':
        user_otp = request.POST.get('otp')

       
        if totp.verify(user_otp, valid_window=0):
            login(request, user)
            request.session.modified = True
            del request.session['otp_secret_key']
            del request.session['username']
            return redirect('index')
        else:
            return render(request, 'login/otp.html', {
                'otp': otp_code,
                'error': 'Invalid or expired OTP.'
            })

    email=EmailMessage(
        f'OTP Code {otp_code}',
        f'Your OTP code is: {otp_code} Description description description',
        settings.EMAIL_HOST_USER,
        [user.email],
        
    )
    email.fail_silently=False

    

    email.send()

    return render(request, 'login/otp.html', {'otp': otp_code})





#user views
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


def user_setting(request):
    return render(request, "login/user_nav/user_setting.html")


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
def admin_calendar(request):
    today=timezone.now().date()
    upcoming_webinars=Webinar.objects.filter(start_date__gte=today ) 
    print(upcoming_webinars)
    return render(request,"login/admin_panel/calendar.html",{
       
        "upcoming_webinars":upcoming_webinars
    })


def admin_certificate(request):
    webinars=Webinar.objects.all()
    today=timezone.now().date()
    
    return render(request, "login/admin_panel/certificate.html",{
        'webinars':webinars,
        'today':today
    })


def admin_events(request):
    webinar=Webinar.objects.all()
    return render(request, "login/admin_panel/events.html",{
        'webinars':webinar,
      
    })


def admin_setting(request):
    return render(request, "login/admin_panel/setting.html")


def admin_users(request):
    users=User.objects.all()
    return render(request, "login/admin_panel/users.html",{
        'users':users
    })


#create user and edit credential
def register_user(request):
    if request.method=="POST":
        full_name=request.POST.get('user_fullname',' ').strip()
        name=full_name.split(" ")
        if not name:
            first_name = ''
            last_name = ''
        elif len(name) == 1:
            first_name = name[0]
            last_name = ''
        else:
            first_name = name[0]
            last_name = ' '.join(name[1:])

        email=request.POST.get("user_email")
        password=request.POST.get("user_password")
        school_id=request.POST.get("school_id")
        username=full_name

        if User.objects.filter(username=username).exists():
            messages.error(request,"username Already Exist")
            return redirect('admin_users')
            
        elif User.objects.filter(email=email).exists():
            messages.error(request,"Email Already Exist")
            return redirect('admin_users')
        else:
            user= User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
            profile=UserProfile.objects.create(user=user, school_id=school_id)
    return redirect('admin_users')


def generete_authorization_key(request):
   
    otp=pyotp.random_base32()
    code=pyotp.TOTP(otp).now()
    request.session['authorization_key']=code

    send_mail(
    'Request for Admin Authorization Code',
    f'''User {request.user} has requested to create an admin account.
    If you approve this request, please share the following authorization code:

    {code}
    ''',
        f'{settings.EMAIL_HOST_USER}',  
        [f'{settings.ADMIN_EMAIL}'], )
    return redirect('admin_users')
            

def create_admin(request):
    if request.method == 'POST':
        if 'authorization_key' not in request.session:
            messages.error(request, 'Please request an Authorization Key before proceeding.')
            return redirect('admin_users')

        if request.POST.get('admin_code') == request.session.get('authorization_key'):
            del request.session['authorization_key']
            full_name = request.POST.get('admin_fullname', '').strip()
            name = full_name.split(" ")
            first_name = name[0] 
            last_name = ' '.join(name[1:])

            email = request.POST.get("admin_email")
            password = request.POST.get("admin_password")
            username = full_name

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
                    password=password
                )
                user.is_staff = True
                user.save()
                messages.success(request, "Admin account created successfully.")
        else:
            messages.error(request, "Invalid authorization code.")

    return redirect('admin_users')


def delete_user(request, id):
    user=User.objects.filter(id=id)
    user.delete()

    return redirect("admin_users")


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
                if request.user.is_staff or request.user.is_admin:
                    redirected=redirection[0]
                else:
                    redirected=redirection[1]

                return render(request, f'login/{redirected}', {
                    'error_password': 'Current password is incorrect.'
                })



def log_list(request):
    logs = LogEntry.objects.filter(user__is_staff=True).order_by('-action_time')
    return render(request, "login/admin_panel/admin_log.html", {"logs": logs})



