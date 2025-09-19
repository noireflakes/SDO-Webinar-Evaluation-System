from django.shortcuts import render,redirect, get_object_or_404
from .models import Webinar,WebinarAttendees,ResponseQuestionaire,Speaker,Test_Question,TestResponse,Choice, Comment
from django.db.models import Avg,F

from django.conf import settings
from django.core import serializers
from django.http import JsonResponse,HttpResponse
import qrcode
from django.contrib import messages 
import re
from login.models import UserProfile
from login.email_service import send_email
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

#create events
def make_webinar(request):
    if request.method=='POST':
        title=request.POST.get('title')
        description=request.POST.get('description')
        number_of_speaker=int(request.POST.get('number_of_speaker'))
        event_type=request.POST.get('event_type')
        custom_event_type=request.POST.get('custom_event_type')
        start_date=request.POST.get('start_date')
        until_date=request.POST.get('until_date')
        time=request.POST.get('event_time')
        banner=request.FILES.get('banner')
        venue=request.POST.get('venue')

        # Use custom event type if "other" is selected and custom type is provided
        if event_type == "other" and custom_event_type:
            event_type = custom_event_type.strip()

        id=request.POST.get('event_id')
        try:
            webinar=Webinar.objects.get(id=id)
            webinar.title=title
            webinar.description=description
            webinar.number_of_speaker=number_of_speaker
            webinar.event_type=event_type
            webinar.start_date=start_date
            webinar.until_date=until_date
            webinar.time=time
            webinar.venue=venue
            if banner:
                webinar.banner=banner
            webinar.save()

            speakers=webinar.speaker.all()
            for i in range(number_of_speaker):
                name = request.POST.get(f'speaker_name{i}', '').strip()
                email = request.POST.get(f'speaker_email{i}', '').strip()
                img = request.FILES.get(f'speaker_photo{i}')

                if i < len(speakers):
                    # Update existing speaker
                    speaker = speakers[i]
                    if name: speaker.name = name
                    if email: speaker.email = email
                    if img: speaker.img = img
                    speaker.save()
                else:
                    # Add new speaker
                    if name or email or img:
                        Speaker.objects.create(
                            webinar=webinar,
                            name=name,
                            email=email,
                            img=img
                        )

        except Webinar.DoesNotExist:
            #save event info
            webinar=Webinar(title=title,
            description=description, number_of_speaker=number_of_speaker, event_type=event_type,
            start_date=start_date, until_date=until_date, time=time, banner=banner,
            venue=venue)
            webinar.save()

            #save speakers
            for i in range(number_of_speaker):
                speaker_name=request.POST.get(f'speaker_name{i}')
                speaker_email=request.POST.get(f'speaker_email{i}')
                img=request.FILES.get(f'speaker_photo{i}')
                speaker=Speaker(webinar=webinar, img=img, name=speaker_name, email=speaker_email)
                speaker.save()

        return redirect('index')
    
    return render(request, 'webinar/makewebinar.html'
    )


def webinar_detail(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    attendees = WebinarAttendees.objects.filter(webinar=webinar)
    
    if request.user.is_authenticated:
        return render(request, "webinar/webinar_detail.html", {
            'webinar': webinar,
            'attendees': attendees 
        })
    
    messages.error(request, "Please Login first to access the Events.")
    return redirect("index")


def edit_events(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    speakers = webinar.speaker.all()  
    
    return render(request, "webinar/makewebinar.html", {
        'webinar': webinar,
        'speakers': speakers 
    })


def events_data(request):
    events = []

    for webinar in Webinar.objects.all():
        events.append({
            'title': webinar.title,
            'start': webinar.start_date.isoformat(),  
            'end': webinar.until_date.isoformat() ,
        })

    return JsonResponse(events, safe=False)


def user_events_data(request):
    events = []
    attendances = WebinarAttendees.objects.filter(user=request.user)

    for attendance in attendances:
        webinar = attendance.webinar  
        events.append({
            'title': webinar.title,
            'start': webinar.start_date.isoformat() if webinar.start_date else None,
            'end': webinar.until_date.isoformat() if webinar.until_date else None,
        })

    return JsonResponse(events, safe=False)


def register(request, id):
    webinar = get_object_or_404(Webinar, id=id)

    attendees = WebinarAttendees.objects.filter(webinar=webinar).order_by("-id")

    if request.method == 'POST':

        email = request.POST.get('email')

        try:
            user=User.objects.get(email=email)
        except User.DoesNotExist:
            print("user not found")
            messages.error(request, "This Email is invalid")
            return redirect("register", webinar.id)
        


        already_registered = WebinarAttendees.objects.filter(webinar=webinar, user=user).exists()

        if already_registered:
            messages.warning(request, "You are already registered for this webinar.")
            return redirect('register', id=webinar.id)

        attendee = WebinarAttendees(webinar=webinar, user=user, email=email)
        attendee.save()

        subject = f"Registration Confirmed: {webinar.title}"
    
        message = f""""
            Hello,\n\n
            You are now registered for \"{webinar.title}\".\n\n
            "📅 Date: {webinar.start_date}\n"
            "📍 Location: {webinar.venue}\n\n"
            "We look forward to seeing you there!\n\n"
            "Best regards,\n"
            "The Webinar Team"
        """
        html_message = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.5;">
    <p>Hello,</p>

    <p>You are now registered for "<strong>{webinar.title}</strong>".</p>

    <p>
      📅 <strong>Date:</strong> {webinar.start_date}<br>
      📍 <strong>Location:</strong> {webinar.venue}
    </p>

    <p>We look forward to seeing you there!</p>

    <p>Best regards,<br>
    The Webinar Team</p>
  </body>
</html>
"""




        send_email(
        to_email=email,
        subject=subject,
        body= html_message
    )

        messages.success(request, "Registration successful!")
        return redirect('register', id=webinar.id)

    return render(request, 'webinar/register.html', {
        'webinar': webinar,
        'attendees': attendees
    })


#validation
def validation(request, id):
    webinar=get_object_or_404(Webinar, id=id)

    if request.method=='POST':
        deped_id=request.POST.get('deped_id')
        email=request.POST.get('email')
        valid= WebinarAttendees.objects.filter(webinar=webinar, deped_id=deped_id, email=email).exists()

        if valid:
            return redirect('questionaire', webinar.id)
        else:
            return redirect('validation', webinar.id)

    return render(request, "webinar/evaluation/validation.html", {
        "id":id
    })

#questionaire
def questionaire(request, id):
    webinar = get_object_or_404(Webinar, id=id)

    speaker = []
    venue = []
    meals = []
    manage = []
    all_responses = {
        "speaker": speaker,
        "venue": venue,
        "meals": meals,
        "manage": manage
    }

    if request.method == 'POST':
        sex = request.POST.get('sex')
        email = request.POST.get('email')
        try:
            user = get_object_or_404(User, email=email)
            attendee = get_object_or_404(WebinarAttendees, user=user, webinar=webinar)
            
            if attendee.attendance < 1:
            
                if request.POST.get('comment'):
                    Comment.objects.create(
                        webinar=webinar,
                        user=user,
                        text=request.POST.get('comment')
                    )

         
                for key, value in request.POST.items():
                    if key.startswith('speaker'):
                        speaker.append(value)
                    elif key.startswith('venue'):
                        venue.append(value)
                    elif key.startswith('meals'):
                        meals.append(value)
                    elif key.startswith("manage"):
                        manage.append(value)

                for category, response in all_responses.items():
                    if response:  
                    
                        while len(response) < 5:
                            response.append(None)

                        ResponseQuestionaire.objects.create(
                            webinar=webinar,
                            user=user,
                            type=category,
                            q1=response[0],
                            q2=response[1],
                            q3=response[2],
                            q4=response[3],
                            q5=response[4],
                            sex=sex
                        )

                attendee.attendance = 1
                attendee.save()

                return redirect("index")

            else:
                error_message = "You already answered"
                messages.error(request, "You already answered")
                return redirect("index")

        except User.DoesNotExist:  
            error_message = "Invalid id please recheck your Deped id"
            
            if webinar.event_type == 'recognition':
                return render(request, 'webinar/evaluation/recognition.html', {
                    'webinar': webinar,
                    'error_message': error_message
                })
            elif webinar.event_type == 'seminar':
                return render(request, 'webinar/evaluation/seminar.html', {
                    'webinar': webinar,
                    'error_message': error_message
                })
            
            return render(request, 'webinar/evaluation/workshop.html', {
                'webinar': webinar,
                'error_message': error_message
            })

    if webinar.event_type == 'recognition':
        return render(request, 'webinar/evaluation/recognition.html', {
            'webinar': webinar
        })
    elif webinar.event_type == 'seminar':
        return render(request, 'webinar/evaluation/seminar.html', {
            'webinar': webinar
        })
    
    return render(request, 'webinar/evaluation/workshop.html', {
        'webinar': webinar
    })


def create_test(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    
    if request.method == 'POST':
        test_type = request.POST.get("test_type")
        q_type = request.POST.get('q_type')
        question_text = request.POST.get('question')

        if q_type == 'FB':
            fb_ans = request.POST.get("FB")
            Test_Question.objects.create(
                webinar=webinar,
                question=question_text,
                test_type=test_type,
                question_type=q_type,
                correct_answered=fb_ans
            )


        elif q_type == 'MC':
            mc_ans = int(request.POST.get("MC_correct",0))
            nc = int(request.POST.get("NC")) 

            question = Test_Question.objects.create(
                webinar=webinar,
                question=question_text,
                test_type=test_type,
                question_type=q_type,
                correct_answered=mc_ans
            )
            print(f"jkfsdoaifwoeu: {question.choices}")

            for i in range( nc + 1):  
                mc_choice = request.POST.get(f"MC_choice_{i}")
                if mc_choice: 
                    if mc_ans==i:
                        Choice.objects.create(
                        question=question,
                        text_option=mc_choice,
                        is_correct=True)
                    else:
                        Choice.objects.create(
                        question=question,
                        text_option=mc_choice,
                        is_correct=False)

        
        return redirect("redirect_create_test", id=id)  

    return redirect("redirect_create_test", id=id)


def redirect_create_test(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    question=Test_Question.objects.filter(webinar=webinar)
    choices=Choice.objects.filter(question__in=question)
    json_choices=serializers.serialize("json", choices)
    q_count=len(question)

    return render(request, "webinar/create_test.html", {
        'id': id,
        'questions': question,
        'choices': json_choices,
        'count': q_count,
        'webinar':webinar
        
    })


def edit_test(request, id):
    webinar=get_object_or_404(Webinar, id=id)
    if request.method== 'POST':
       inputs=request.POST.keys()
       for input in inputs:
            if re.search("question_", input):
                edit_question=input
                search_id=re.findall(r"\d+", edit_question)[0]
                question_text=request.POST.get(f"question_{search_id}")
        
                test=Test_Question.objects.get(id=search_id)
                q_type=request.POST.get(f"question_type_{search_id}")
                print(f"question type: {q_type}")
                if q_type == 'FB':
                    print("qtype works")
                    answered = request.POST.get(f"fb_ans_{search_id}")
                    test.question=question_text
                    test.correct_answered=answered
                    print(f"text: {question_text}")
                    print(f"text: {answered}")
                    print(f"id: {search_id}")
                    
                elif q_type == 'MC':  
                    answered = request.POST.get(f"option_{search_id}")
                    test.question=question_text
                    test.correct_answered=answered
                test.save()

                
            elif re.search("option_", input):
                choice_id = re.findall(r"\d+", input)[0]

                text_option = request.POST.get(f'text_option_{choice_id}', '')

                try:

                    
                    option = Choice.objects.get(id=choice_id)
                    question_id = option.question.id  

                   
                    selected_choice_id = request.POST.get(f"option_{question_id}") 
                    is_correct = (str(option.id) == selected_choice_id)

                    
                    option.text_option = text_option
                    option.is_correct = is_correct
                    option.save()
                except Choice.DoesNotExist:
                    continue  

    return redirect(redirect_create_test, id=id)


def delete_question(request, id):
    print(f"this is the delete id {id}")
    test=Test_Question.objects.get(id=id)
     
    test.delete()
    
    return redirect(redirect_create_test, id=test.webinar.id)

def record_test(request, id, type):
    webinar = Webinar.objects.get(id=id)
    questions = webinar.question.filter(test_type=type)
    
    if request.method == 'POST':
        email = request.POST.get("email")
        
        try:
            user = User.objects.get(email=email)
            if not webinar.attendees.filter(user=user).exists():
                return redirect("webinar_detail", id)
            
            responses = []
            for key, value in request.POST.items():
                if key.startswith('user_input_'):
                    q_id = key.split('_')[-1]
                    
                    try:
                        question = Test_Question.objects.get(id=q_id)
                        
                        responses.append(TestResponse(
                            user=user,
                            question=question,
                            user_input=value,
                        ))
                    except Test_Question.DoesNotExist:
                        continue
            
            if responses:
                TestResponse.objects.bulk_create(responses)
                
              
                attendee = webinar.attendees.get(user=user)
                if type == 'pre_test':
                    attendee.pre_test_completion = True
                elif type == 'post_test':
                    attendee.post_test_completion = True
                attendee.save()
            
            return redirect("test_result", webinar.id, type, user.id)
            
        except User.DoesNotExist: 
            return redirect("display_test", id, type)
    
    return redirect("test_result", webinar.id, type, user.id)

@login_required
def close_webinar_evaluation(request, webinar_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('user_dashboard')
    
    webinar = get_object_or_404(Webinar, id=webinar_id)
    
    if request.method == 'POST':
        # Close the evaluation
        webinar.close_evaluation = True
        webinar.save()
        
        messages.success(request, f"All evaluations for '{webinar.title}' have been closed successfully.")
        return redirect('admin_dashboard')
    
    return render(request, 'admin/close_evaluation_confirm.html', {
        'webinar': webinar
    })

from django.utils import timezone
from datetime import timedelta

@login_required
def toggle_evaluation_ajax(request, webinar_id):

    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    webinar = get_object_or_404(Webinar, id=webinar_id)
    
    # Toggle the status
    webinar.close_evaluation = not webinar.close_evaluation
    webinar.save()
    
    status = "closed" if webinar.close_evaluation else "opened"
    
    return JsonResponse({
        'success': True,
        'status': status,
        'closed': webinar.close_evaluation,
        'message': f"Evaluation has been {status}."
    })


from django.utils import timezone
from datetime import timedelta

def check_attendance(request, id, test_type='evaluation'):
    webinar = get_object_or_404(Webinar, id=id)

    if webinar.close_evaluation:
        test_name = test_type.replace('_', ' ').title()
        messages.error(request, f"The {test_name} is closed for this webinar.")
        return render(request, "webinar/validate.html", {
            "webinar": webinar,
            "test_type": test_type,
            "closing": True
        })
    
    valid_test_types = ['evaluation', 'pre_test', 'post_test']
    if test_type not in valid_test_types:
        messages.error(request, "Invalid test type")
        return redirect("webinar_detail", webinar.id)

    if request.method == 'POST':
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                try:
                    attendee = WebinarAttendees.objects.get(webinar=webinar, user=user)
                    completion_check = {
                        'evaluation': attendee.attendance > 0,
                        'pre_test': attendee.pre_test_completion,
                        'post_test': attendee.post_test_completion
                    }
                    
                    if completion_check.get(test_type, False):
                        test_name = test_type.replace('_', '-')
                        messages.error(request, f"You already completed the {test_name}")
                        return redirect("check_attendance", webinar.id, test_type)
                    
                    if test_type in ['pre_test', 'post_test']:
                        return redirect("display_test", id=webinar.id, type=test_type, user_id=user.id)
                    
                    return render(request, f'webinar/evaluation/{webinar.event_type}.html', {
                        'webinar': webinar,
                        'user': user,
                    })

                except WebinarAttendees.DoesNotExist:
                    messages.error(request, "User is not on the attendance list")
                    return redirect("check_attendance", webinar.id, test_type)
            else:
                messages.error(request, "Incorrect password")
                return redirect("check_attendance", webinar.id, test_type)

        except User.DoesNotExist:
            messages.error(request, "No user found with that email")
            return redirect("check_attendance", webinar.id, test_type)

    return render(request, "webinar/validate.html", {
        "webinar": webinar,
        "test_type": test_type,
        "closing": False
    })