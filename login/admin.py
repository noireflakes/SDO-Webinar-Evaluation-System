from django.contrib import admin
from .models import UserProfile,TrustedDevice
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(TrustedDevice)
