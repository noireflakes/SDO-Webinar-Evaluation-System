from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from cloudinary_storage.storage import MediaCloudinaryStorage
# Create your models here.

class Webinar(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    number_of_speaker = models.IntegerField(default=1)
    event_type = models.CharField(max_length=20, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    until_date = models.DateField(null=True, blank=True)
    time = models.TimeField(max_length=20)
    banner = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='banner')
    venue = models.CharField(max_length=500)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Webinar.objects.get(pk=self.pk)
                if old_instance.banner and old_instance.banner != self.banner:
                    old_instance.banner.delete(save=False)
            except Webinar.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.id)} - {self.title}"


class Speaker(models.Model):
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="speaker")
    img = models.ImageField(
        storage=MediaCloudinaryStorage(), 
        upload_to="SpeakerProfile", 
        blank=True, 
        default='UserProfile/1.jpg', 
        null=True
    )
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=250, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Speaker.objects.get(pk=self.pk)
                if (old_instance.img and 
                    old_instance.img != self.img and 
                    old_instance.img.name != 'UserProfile/1.jpg'):
                    old_instance.img.delete(save=False)
            except Speaker.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WebinarAttendees(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="attendees")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendees", null=True, blank=True)
    deped_id=models.CharField(max_length=80, null=True)
    email=models.EmailField()
    attendance=models.IntegerField(default=0) 
    pre_test_completion=models.BooleanField(default=False) 
    post_test_completion=models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.webinar}-{self.user}"


class ResponseQuestionaire(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="evaluation")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="response")
    type=models.CharField(max_length=100, null=True, blank=True)
    sex=models.CharField(max_length=50, null=True, blank=True)
    q1=models.IntegerField(null=True)
    q2=models.IntegerField(null=True)
    q3=models.IntegerField(null=True)
    q4=models.IntegerField(null=True)
    q5=models.IntegerField(null=True)
    q6=models.IntegerField(null=True)
    timestamp=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}-{self.type}"

    
class Comment(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="comment")
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment")
    text=models.TextField()
    
    def __str__(self):
        return f"{self.webinar}-{self.user}"


class Test_Question(models.Model):
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, blank=True, null=True ,related_name="question")
    question = models.CharField(max_length=500 , blank=True, null=True)
    test_type = models.CharField(max_length=100, blank=True, null=True) 
    question_type = models.CharField(max_length=100, blank=True, null=True) 
    correct_answered = models.CharField(max_length=200, blank=True, null=True)  

    def __str__(self):
        return f" {self.webinar}- {self.test_type}"

class Choice(models.Model):
    question=models.ForeignKey(Test_Question,related_name="choices", on_delete=models.CASCADE,blank=True, null=True)
    text_option=models.CharField(max_length=200, blank=True, null=True)
    is_correct=models.BooleanField(default=False)

    def __str__(self):
        return self.question




class TestResponse(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True )
    question=models.ForeignKey(Test_Question, on_delete=models.CASCADE,blank=True, null=True, related_name='test_reponse')
    user_input=models.CharField(max_length=200,blank=True, null=True)
    is_correct=models.BooleanField(default=False)

    def __str__(self):
        return self.user

