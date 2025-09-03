from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.utils import timezone
# Create your models here.
class UserProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='UserProfile', null=True, blank=True , default='UserProfile/defaultprofile_ntxlw1.jpg',)
    deped_id=models.CharField(max_length=100, null=True, blank=True)
    number=models.CharField(max_length=100, null=True, blank=True)
    school=models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return self.user.first_name

class TrustedDevice(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,  related_name="trusted_device")
    hash=models.CharField(max_length=500)
    timestamp=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name}_{self.id}"
    
    
class Otp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    secret_key=models.CharField(max_length=40)
    
    created_at = models.DateTimeField(auto_now_add=True)
    retry = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(null=True, blank=True)  
    def __str__(self):
        return f"{self.id}-{self.user}-{self.otp}"

