from django.urls import path
from . import views

urlpatterns = [
    path('test_result/<int:web_id>/<str:type>/<int:id>/',views.test_result, name='test_result'), 
    path("result_data/<int:id>/", views.result_data, name="result_data"),
    path("rounded_data/<int:id>/", views.rounded_data, name="rounded_data"),
    path("display_result/<int:id>/", views.display_result , name="display_result"),
    path("test_score/<int:id>/<str:type>/", views.test_score, name="test_score"),
    path("test_data/<int:id>/", views.test_data, name="test_data"),
    path("attendees_data/<int:id>/", views.attendees_data, name="attendance_data"),
   
   
    path("generate_qr/<int:id>/<str:type>/", views.generate_qr , name="generate_qr"),
    path("qr_evalution/<int:id>/", views.qr_evalution, name="qr_evalution"),
    path("display_qr/<int:id>/<str:type>/", views.display_qr , name="display_qr"),
    path("display_test/<int:id>/<str:type>/<int:user_id>", views.display_test , name="display_test"),


    path("create_certificate/<int:id>/", views.create_certificate, name="create_certificate"),
    path("redirect_certificate/<int:id>/", views.redirect_certificate , name="redirect_certificate"),
    path("upload_img/<int:id>/", views.upload_img , name="upload_img"),
    path("cert_preview/<int:id>/", views.cert_preview, name="cert_preview"),

    path("display_qr/<int:id>/", views.display_qr , name="display_qr"),
    path("upload_contents/<int:id>/", views.save_certificate , name="upload_contents"),

]