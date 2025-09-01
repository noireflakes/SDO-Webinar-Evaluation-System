from auditlog.registry import auditlog
from django.contrib.auth.models import User
from webinar.models import Webinar,WebinarAttendees
from exam_portal.models import CertificateTemplate,EvalQR,TestQR
from login.models import UserProfile


auditlog.register(User)
auditlog.register(Webinar)
auditlog.register(WebinarAttendees)
auditlog.register(CertificateTemplate)
auditlog.register(EvalQR)
auditlog.register(TestQR)
auditlog.register(UserProfile)