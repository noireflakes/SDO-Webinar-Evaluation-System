from django.contrib import admin
from .models import TestQR, CertificateTemplate,TestResult,EvalQR


admin.site.register(TestQR)
admin.site.register(CertificateTemplate)
admin.site.register(TestResult)
admin.site.register(EvalQR)


# Register your models here.
