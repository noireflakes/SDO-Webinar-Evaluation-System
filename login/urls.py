from django.urls import path
from . import views

urlpatterns=[
    #login handler path
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("verification/<int:user_id>/", views.generate_otp, name="otp"),


  
    #admin path
    path("admin_events",views.admin_events, name="admin_events"),
    path("admin_calendar",views.admin_calendar, name="admin_calendar"),
    path("admin_certificate",views.admin_certificate, name="admin_certificate"),
    path("admin_setting",views.admin_setting, name="admin_setting"),
    path("admin_users",views.admin_users, name="admin_users"),
    path("admin_log", views.log_list, name="admin_log" ),

    #user path
    path("user_dashboard", views.user_dashboard, name="user_dashboard"),
    path("calendar", views.calendar, name="calendar"),
    path("certificate", views.certificate, name="certificate"),
    path("certificate_data/<int:id>/", views.certificate_data, name="certificate_data"),
    path("user_setting", views.user_setting, name="user_setting"),

    #create and edit user
    path("register_user", views.register_user, name="register_user"),
    path("create_admin", views.create_admin, name="create_admin"),
    path('delete_user/<int:id>/', views.delete_user, name="delete_user"),
    path("generete_authorization_key", views.generete_authorization_key, name="generete_authorization_key"),
    path("edit_user", views.edit_user, name="edit_user"),
    path("Change_password", views.change_password, name="change_password"),



    

    
]