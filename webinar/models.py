from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Webinar(models.Model): 
    title=models.CharField(max_length=100)
    description=models.CharField(max_length=1000)
    number_of_speaker=models.IntegerField(default=1)
    event_type=models.CharField(max_length=20, null=True ,blank=True)
    start_date=models.DateField(null=True ,blank=True)
    until_date=models.DateField(null=True, blank=True)
    time=models.TimeField(max_length=20)
    banner=models.ImageField(upload_to='banner')
    venue=models.CharField(max_length=40)

    def __str__(self):
        return f"{self.title} - {self.venue}"

class Speaker(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="speaker")
    img=models.ImageField(upload_to="SpeakerProfile",blank=True,default='UserProfile/1.jpg', null=True)
    name=models.CharField(max_length=30)
    email=models.EmailField(max_length=30, null=True)


class WebinarAttendees(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="attendees")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendees", null=True, blank=True)
    school_id=models.CharField(max_length=20, null=True)
    email=models.EmailField()
    attendance=models.IntegerField(default=0)


class ResponseQuestionaire(models.Model):
      webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="evaluation")
      user=models.ForeignKey(User, on_delete=models.CASCADE)
      type=models.CharField(max_length=100, null=True, blank=True)
      q1=models.IntegerField(null=True)
      q2=models.IntegerField(null=True)
      q3=models.IntegerField(null=True)
      q4=models.IntegerField(null=True)
      q5=models.IntegerField(null=True)
      q6=models.IntegerField(null=True)


class Comment(models.Model):
    Webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="comment")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment")
    text=models.TextField()


class Test_Question(models.Model):
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, blank=True, null=True ,related_name="question")
    question = models.CharField(max_length=500 , blank=True, null=True)
    test_type = models.CharField(max_length=30, blank=True, null=True) 
    question_type = models.CharField(max_length=50, blank=True, null=True) 
    correct_answered = models.CharField(max_length=200, blank=True, null=True)  

class Choice(models.Model):
    question=models.ForeignKey(Test_Question,related_name="choices", on_delete=models.CASCADE,blank=True, null=True)
    text_option=models.CharField(max_length=200, blank=True, null=True)
    is_correct=models.BooleanField(default=False)



class TestResponse(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True )
    question=models.ForeignKey(Test_Question, on_delete=models.CASCADE,blank=True, null=True, related_name='test_reponse')
    user_input=models.CharField(max_length=200,blank=True, null=True)
    is_correct=models.BooleanField(default=False)

