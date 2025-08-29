from django.core.mail import send_mail
from django.conf import settings
import ssl, certifi
from django.core.mail import get_connection

def send_otp_email(recipient_email, otp_code):
    context = ssl.create_default_context(cafile=certifi.where())

    connection = get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=True,
        ssl_context=context
    )

    send_mail(
        'OTP code From SDO',
        f'Enter this to confirm your Login: {otp_code}',
        settings.EMAIL_HOST_USER,
        [recipient_email],
        connection=connection,
        fail_silently=False
    )