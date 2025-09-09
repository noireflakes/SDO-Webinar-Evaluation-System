from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.utils import timezone
import uuid
# Create your models here.
class UserProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    img=models.ImageField(storage=MediaCloudinaryStorage(),upload_to='UserProfile', null=True, blank=True , default='UserProfile/defaultprofile_ntxlw1.jpg',)
    deped_id=models.CharField(max_length=100, null=True, blank=True)
    number=models.CharField(max_length=100, null=True, blank=True)
    school=models.CharField(max_length=100, null=True, blank=True)
    birthday=models.DateField(default=timezone.now)

    #delete old img 
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = UserProfile.objects.get(pk=self.pk)
                if (old_instance.img and 
                    old_instance.img != self.img and 
                    old_instance.img.name != 'UserProfile/defaultprofile_ntxlw1.jpg'):
                    old_instance.img.delete(save=False)
            except UserProfile.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.first_name

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
    secret_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    retry = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(null=True, blank=True)
    is_valid = models.BooleanField(default=True, null=True, blank=True)
    

    lockout_until = models.DateTimeField(null=True, blank=True)
    total_failed_attempts = models.IntegerField(default=0) 
    
    def __str__(self):
        return f"{self.id}-{self.user}-{self.otp}"
    
    def is_locked_out(self):
        
        if self.lockout_until:
            return timezone.now() < self.lockout_until
        return False
    
    def get_lockout_remaining_seconds(self):
       
        if self.lockout_until and self.is_locked_out():
            return int((self.lockout_until - timezone.now()).total_seconds())
        return 0
    
    def clear_lockout(self):

        self.lockout_until = None
        self.total_failed_attempts = 0
        self.save()

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 3600  

