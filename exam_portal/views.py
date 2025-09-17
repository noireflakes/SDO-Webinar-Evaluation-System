from django.shortcuts import render
from webinar.models import Test_Question, TestResponse, ResponseQuestionaire,Webinar,WebinarAttendees,Choice
from .models import TestResult,TestQR, CertificateTemplate, EvalQR
from django.shortcuts import redirect, get_object_or_404
import json
from django.core.files.base import ContentFile
from django.http import JsonResponse
from .serializer import CertificateSerilize
import qrcode
from collections import Counter
from io import BytesIO
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from webinar.models import Comment
from django.contrib import messages 

#decorator
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url="login")(view_func)

def user_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and not u.is_staff)(view_func)


def test_result(request, web_id, type, id):
    webinar=get_object_or_404(Webinar, id=web_id)
    user=get_object_or_404(User, id=id)
    test_responses = TestResponse.objects.filter(
        user=id,
        question__webinar=webinar,
        question__test_type=type
    )
    score = 0
    for response in test_responses:
        question = response.question
        correct = question.correct_answered
        if question.question_type == 'MC':
            try:
                selected_choice = Choice.objects.get(id=response.user_input)
                if selected_choice.is_correct:
                    score += 1
            except Choice.DoesNotExist:
                continue
        else:
            if response.user_input == correct:
                score += 1
    TestResult.objects.create(
        webinar=webinar,
        user=user,
        test=type,
        score=score
    )
    return redirect("index")


@admin_required
def display_result(request, id):
    webinar = Webinar.objects.get(id=id)
    test_results = TestResult.objects.filter(webinar=webinar)
    evaluations = ResponseQuestionaire.objects.filter(webinar=webinar)
    comments = Comment.objects.filter(webinar=webinar).select_related('user')
    
    evaluation_responses = []
    pre_test_result = []
    post_test_result = []
    
    return render(request, 'exam_portal/statistics.html', {
        'webinar': webinar,
        'comments': comments
    })

@admin_required
def attendees_data(request, id):
    webinar = get_object_or_404(Webinar, id=id)
    
    attendees = WebinarAttendees.objects.filter(webinar=webinar).select_related('user')
    
    attendees_list = []
    for attendee in attendees:
       
        questionnaire_response = ResponseQuestionaire.objects.filter(
            webinar=webinar,
            user=attendee.user
        ).first()
        
        attendees_list.append({
            'email': attendee.email,
            'deped_id': attendee.deped_id or '',
            'attendance': attendee.attendance,
            'pre_test_completion': attendee.pre_test_completion,
            'post_test_completion': attendee.post_test_completion,
            'user_id': attendee.user.id if attendee.user else None,
            'evaluation_timestamp': questionnaire_response.timestamp if questionnaire_response else None,
        })
    
    return JsonResponse({
        'attendees': attendees_list
    })

def rounded_data(request, id):
    webinar = get_object_or_404(Webinar, id=id)

    speaker = []
    venue = []
    meals = []
    manage = []

    for evaluation in webinar.evaluation.all():
        total = [evaluation.q1, evaluation.q2, evaluation.q3, evaluation.q4, evaluation.q5, evaluation.q6]
        valid_number = [s for s in total if s is not None]
        average = sum(valid_number) / len(valid_number) if valid_number else 0
        average = round(average)

        if evaluation.type == 'speaker':
            speaker.append(average)
        elif evaluation.type == 'venue':
            venue.append(average)
        elif evaluation.type == 'meals': 
            meals.append(average)
        elif evaluation.type == 'manage':
            manage.append(average)

  
    speaker_counter = Counter(speaker)
    venue_counter = Counter(venue)
    meal_counter = Counter(meals)
    manage_counter = Counter(manage)

 
    overall = speaker + venue + meals + manage
    overall_counter = Counter(overall)

    evaluations = {
        "speaker": [speaker_counter.get(5,0), speaker_counter.get(4,0), speaker_counter.get(3,0), speaker_counter.get(2,0), speaker_counter.get(1,0)],
        "venue":   [venue_counter.get(5,0), venue_counter.get(4,0), venue_counter.get(3,0), venue_counter.get(2,0), venue_counter.get(1,0)],
        "meals":    [meal_counter.get(5,0), meal_counter.get(4,0), meal_counter.get(3,0), meal_counter.get(2,0), meal_counter.get(1,0)],
        "manage":  [manage_counter.get(5,0), manage_counter.get(4,0), manage_counter.get(3,0), manage_counter.get(2,0), manage_counter.get(1,0)],
        "overall": [overall_counter.get(5,0), overall_counter.get(4,0), overall_counter.get(3,0), overall_counter.get(2,0), overall_counter.get(1,0)]
    }
    print(evaluations)

    return JsonResponse(evaluations)


def result_data(request, id):     
    webinar = get_object_or_404(Webinar, id=id)
           
    # Evaluation data     
    email = []     
    deped_id = []     
    sex = []     
    timestamps = []     
    speaker = []     
    venue = []     
    meal = []     
    manage = []       

    # Attendance data     
    attendance_emails = []
    attendance_deped_ids = []     
    attendance_scores = []          

    # Comments data     
    comment_emails = []     
    comment_deped_ids = []     
    comment_texts = []     
    comment_timestamps = []      

    # Group evaluations by user to avoid duplicates
    user_evaluations = {}
    
    # First, collect all evaluations and group by user
    for evaluation in webinar.evaluation.all():
        user_email = evaluation.user.email
        
        if user_email not in user_evaluations:
            user_evaluations[user_email] = {
                'user': evaluation.user,
                'sex': evaluation.sex,
                'timestamp': evaluation.timestamp,
                'speaker': [],
                'venue': [],
                'meal': [],
                'manage': []
            }
        
        # Group scores by type
        total = [evaluation.q1, evaluation.q2, evaluation.q3, evaluation.q4, evaluation.q5]
        valid_numbers = [s for s in total if s is not None]
        average = sum(valid_numbers) / len(valid_numbers) if valid_numbers else 0
        
        if evaluation.type == 'speaker':
            user_evaluations[user_email]['speaker'].append(average)
        elif evaluation.type == 'venue':
            user_evaluations[user_email]['venue'].append(average)
        elif evaluation.type == 'meals':
            user_evaluations[user_email]['meal'].append(average)
        elif evaluation.type == 'manage':
            user_evaluations[user_email]['manage'].append(average)
    
    # Now create one entry per user
    for user_email, data in user_evaluations.items():
        email.append(user_email)
        deped_id.append(data['user'].user_profile.deped_id)
        sex.append(data['sex'])
        timestamps.append(data['timestamp'])
        
        # Calculate average for each category (in case there are multiple scores)
        speaker_avg = sum(data['speaker']) / len(data['speaker']) if data['speaker'] else 0
        venue_avg = sum(data['venue']) / len(data['venue']) if data['venue'] else 0
        meal_avg = sum(data['meal']) / len(data['meal']) if data['meal'] else 0
        manage_avg = sum(data['manage']) / len(data['manage']) if data['manage'] else 0
        
        speaker.append(speaker_avg)
        venue.append(venue_avg)
        meal.append(meal_avg)
        manage.append(manage_avg)

    # Process attendance     
    for attendee in webinar.attendees.all():         
        attendance_emails.append(attendee.email)         
        attendance_deped_ids.append(attendee.deped_id)         
        attendance_scores.append(attendee.attendance)          

    # Process comments     
    for comment in webinar.comment.all():         
        comment_emails.append(comment.user.email)         
        try:             
            comment_deped_ids.append(comment.user.user_profile.deped_id)         
        except AttributeError:             
            comment_deped_ids.append("")                          
        comment_texts.append(comment.text)                          

        if hasattr(comment, 'timestamp'):             
            comment_timestamps.append(comment.timestamp)         
        else:             
            comment_timestamps.append("")               

    overall = speaker + venue + meal + manage      

    # Combined response data     
    response_data = {         
        # Evaluation data         
        "email": email,         
        "deped_id": deped_id,         
        "sex": sex,                                  
        "timestamp": timestamps,                     
        "speaker": speaker,         
        "venue": venue,         
        "meal": meal,         
        "manage": manage,         
        "overall": overall,                          

        # Attendance data         
        "attendance_emails": attendance_emails,         
        "attendance_deped_ids": attendance_deped_ids,         
        "attendance_scores": attendance_scores,                          

        # Comments data         
        "comment_emails": comment_emails,         
        "comment_deped_ids": comment_deped_ids,         
        "comment_texts": comment_texts,         
        "comment_timestamps": comment_timestamps,     
    }      
    print("evaluation")

    return JsonResponse(response_data)


def test_data(request, id):
    webinar=get_object_or_404(Webinar, id=id)
    test_result=[]
    results=webinar.test_result.all()
    
    for result in results:
        test_result.append({
            "user":result.user.email,
            "deped_id":result.user.user_profile.deped_id,
            "test_type":result.test,
            "score":result.score
        })
    
    return JsonResponse({"test_result":test_result})


def test_score(request, id, type):
    webinar = get_object_or_404(Webinar, id=id)
    scores = []

  
    test_score = webinar.test_result.filter(test=type)

    for score in test_score:
        scores.append(score.score)
    
    score_count = Counter(scores)

    return JsonResponse({"scores": dict(score_count)})

    

def generate_qr(request, id, type):
    url = 'https://sdo-webinar-evaluation-system.xyz'
    
    qr=TestQR.objects.filter(test__id=id, type=type)


    if not qr:
        
        webinar=Webinar.objects.get(id=id)
        url_path=f'{url}/webinar/check_attendance/{id}/{type}'
        qr = qrcode.make(url_path)
        
        # Save to database
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_img = buffer.getvalue()
        

        qr_db = TestQR.objects.create(
            test=webinar,
            type=type,
            name=f'QR_test_{id}'
        )
        qr_db.img.save(
            f'QR_TEST_ID_{id}.png', ContentFile(qr_img))
        
    return redirect('display_qr', id, type)


@admin_required
def qr_evalution(request, id):
    webinar=get_object_or_404(Webinar, id=id)
    type=webinar.event_type
    qr=EvalQR.objects.filter(test__id=id, type=type)
    
    url=f"https://sdo-webinar-evaluation-system.xyz/webinar/check_attendance/{webinar.id}/evaluation/"

    if not qr:
        
        webinar=Webinar.objects.get(id=id)
        url_path=url
        qr = qrcode.make(url_path)
        
        # Save to database
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_img = buffer.getvalue()
        

        qr_db = EvalQR.objects.create(
            test=webinar,
            type=type,
            name=f'QR_test_{id}'
        )
        qr_db.img.save(
            f'QR_TEST_ID_{id}.png', ContentFile(qr_img))
        
    return redirect('display_qr', id, type)


@admin_required
def display_qr(request, id, type):
    try:
        qr=TestQR.objects.get(test__id=id, type=type)
    except TestQR.DoesNotExist:
        qr=EvalQR.objects.get(test__id=id, type=type)
    return render(request, 'exam_portal/display_qr.html',{
        'qr':qr
    })
        
        

def display_test(request, id, type, user_id):
    webinar = get_object_or_404(Webinar, id=id)
    user = get_object_or_404(User, id=user_id)
    
  
    valid_test_types = ['pre_test', 'post_test']
    if type not in valid_test_types:
        messages.error(request, "Invalid test type")
        return redirect("webinar_detail", webinar.id)
    
    try:
        attendee = WebinarAttendees.objects.get(webinar=webinar, user=user)
        
        if type == 'pre_test' and attendee.pre_test_completion:
            messages.error(request, "You already completed the pre-test")
            return redirect("check_attendance", webinar.id, type)
        elif type == 'post_test' and attendee.post_test_completion:
            messages.error(request, "You already completed the post-test")
            return redirect("check_attendance", webinar.id, type)
            
    except WebinarAttendees.DoesNotExist:
        messages.error(request, "User is not on the attendance list")
        return redirect("check_attendance", webinar.id, type)

    questions = webinar.question.filter(test_type=type)
    
    if not questions.exists():
        messages.error(request, f"No questions found for {type.replace('_', '-')}")
        return redirect("check_attendance", webinar.id, type)
    
    return render(request, "exam_portal/display_test.html", {
        "questions": questions,
        "webinar": webinar,
        "user": user,       
        "attendee": attendee,   
        "id": id,
        "type": type
    })


@admin_required
def create_certificate(request,id):
    webinar=Webinar.objects.get(id=id)
    try:

        certificate=CertificateTemplate.objects.get(webinar=webinar)
        return redirect("redirect_certificate", certificate.id)

        
    except CertificateTemplate.DoesNotExist:

        return render(request, 'exam_portal/createCertificate.html', {
            "webinar":webinar
            })


@admin_required
def redirect_certificate(request, id):
    img=CertificateTemplate.objects.get(id=id)
    messages=""

    if request.session.pop('apply_edit', False):
        messages="The Changes has Been Apllied"
    else:
        messages=""

    return render(request, 'exam_portal/createCertificate.html', {
            'img':img,
            'webinar':img.webinar,
            "messages":messages
        })


def upload_img(request, id):
    if request.method=='POST':
        webinar=Webinar.objects.get(id=id)
        img=request.FILES["img"]

        try:
            img_save=CertificateTemplate.objects.get(webinar=webinar)
            img_save.img=img
            img_save.save()

        except CertificateTemplate.DoesNotExist:
            img_save=CertificateTemplate.objects.create(
                webinar=webinar,
                img=img,
            )
        
        return redirect("redirect_certificate", img_save.id)
        

def save_certificate(request, id):
    if request.method=='POST':
        title=request.POST.get("certificate-title").strip(" ")
        subtitle=request.POST.get("certificate-subtitle").strip(" ")
        participant=request.POST.get("certificate-name").strip(" ")
        host=request.POST.get("certificate-host").strip(" ")
        subject=request.POST.get("certificate-subject").strip(" ")
        address=request.POST.get("certificate-address").strip(" ")
        date=request.POST.get("certificate-date").strip(" ")


        certificate=CertificateTemplate.objects.get(id=id)
        certificate.title=title
        certificate.subtitle=subtitle
        certificate.participant=participant
        certificate.host=host
        certificate.subject=subject
        certificate.address=address
        certificate.date=date
        certificate.save()

        request.session['apply_edit']=True

        return redirect('redirect_certificate', certificate.id)


def cert_preview(request, id):
    webinar=get_object_or_404(Webinar, id=id)
    cert=get_object_or_404(CertificateTemplate, webinar=webinar)
    
    cert_dic=CertificateSerilize(cert).data
    cert_json=json.dumps(cert_dic)

    return render(request, 'exam_portal/certificatepreview.html', {
        'certificate':cert_json

    })