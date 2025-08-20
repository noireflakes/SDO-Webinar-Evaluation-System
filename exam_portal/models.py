from django.db import models
from django.contrib.auth.models import User
from webinar.models import ResponseQuestionaire, TestResponse, Webinar,Test_Question
from cloudinary_storage.storage import MediaCloudinaryStorage

# Create your models here.

class TestResult(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, blank=True, null=True, related_name="test_result")
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    test=models.CharField(max_length=50)
    score=models.IntegerField()


    def __str__(self):
        return self.test


class TestQR(models.Model):
    test=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="test_qr")
    type=models.CharField(max_length=40, null=True, blank=True)
    name=models.CharField(max_length=50)
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='test_qr/')

    def __str__(self):
        return f"{self.type} -{self.test}"
    

class EvalQR(models.Model):
    test=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name="eval_qr")
    type=models.CharField(max_length=40, null=True, blank=True)
    name=models.CharField(max_length=50)
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='eval_qr/')

    def __str__(self):
        return {self.name}

class CertificateTemplate(models.Model):
    webinar=models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='certificate')
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='CertificateTemplate/')
    title=models.CharField(max_length=100, blank=True, null=True )
    subtitle=models.CharField(max_length=100, blank=True, null=True)
    participant=models.CharField(max_length=100, blank=True, null=True)
    host=models.CharField(max_length=100, blank=True, null=True)
    subject=models.TextField( blank=True, null=True)
    address=models.TextField( blank=True, null=True)
    date=models.TextField( blank=True, null=True)

    def __str__(self):
        return f"{self.title} -{self.webinar}"


