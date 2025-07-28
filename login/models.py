from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import MediaCloudinaryStorage
# Create your models here.
class UserProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='UserProfile', null=True, blank=True , default='UserProfile/1.jpg')
    school_id=models.CharField(max_length=100, null=True, blank=True)
    number=models.CharField(max_length=100, null=True, blank=True)
    school=models.CharField(max_length=100, null=True, blank=True)

