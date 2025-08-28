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
    webinar=Webinar.objects.get(id=id)
    test_results=TestResult.objects.filter(webinar=webinar)
    evaluations=ResponseQuestionaire.objects.filter(webinar=webinar)

    evaluation_responses=[]
    pre_test_result=[]
    post_test_result=[]


    return render(request, 'exam_portal/statistics.html',{
        'webinar':webinar
       
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
    email = []
    school_id = []
    sex = []
    timestamps = []
    speaker = []
    venue = []
    meal = []
    manage = []

    for evaluation in webinar.evaluation.all():
        # User details
        email.append(evaluation.user.email)
        school_id.append(evaluation.user.user_profile.school_id)
        sex.append(evaluation.sex)  
        timestamps.append(evaluation.timestamp)     
        
        # Average per evaluation type
        total = [evaluation.q1, evaluation.q2, evaluation.q3, evaluation.q4, evaluation.q5, evaluation.q6]
        valid_number = [s for s in total if s is not None]
        average = sum(valid_number) / len(valid_number) if valid_number else 0

        if evaluation.type == 'speaker':
            speaker.append(average)
        elif evaluation.type == 'venue':
            venue.append(average)
        elif evaluation.type == 'meals':
            meal.append(average)
        elif evaluation.type == 'manage':
            manage.append(average)

    overall = speaker + venue + meal + manage

    evaluations = {
        "email": email,
        "school_id": school_id,
        "sex": sex,                 
        "timestamp": timestamps,    
        "speaker": speaker,
        "venue": venue,
        "meal": meal,
        "manage": manage,
        "overall": overall,
    }

 

    return JsonResponse(evaluations)


def test_data(request, id):
    webinar=get_object_or_404(Webinar, id=id)
    test_result=[]
    results=webinar.test_result.all()
    
    for result in results:
        test_result.append({
            "user":result.user.email,
            "school_id":result.user.user_profile.school_id,
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
    url = 'https://sdo-webinar-evaluation-system-production.up.railway.app/'
    
    qr=TestQR.objects.filter(test__id=id, type=type)


    if not qr:
        
        webinar=Webinar.objects.get(id=id)
        url_path=f'{url}/webinar/display_test/{id}/{type}'
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
    
    url=f"https://sdo-webinar-evaluation-system-production.up.railway.app/webinar/questionaire/{webinar.id}/"

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
        
        
def display_test(request, id, type):
    webinar=Webinar.objects.get(id=id)

    question=webinar.question.filter(test_type=type)
    
    return render(request, "exam_portal/display_test.html", {
        "questions":question,
        "id":id,
        "type":type
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