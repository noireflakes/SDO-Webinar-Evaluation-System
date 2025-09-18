from django.urls import path
from . import views

urlpatterns=[
    #login handler path
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("verification/<int:user_id>/", views.generate_otp, name="otp"),
    path('resend-otp/<int:user_id>/', views.resend_otp, name='resend_otp'),


  
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

    #new_password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uuid:token>/', views.reset_password, name='reset_password'),


    path('cal_event_data/<int:id>/', views.cal_event_data, name='cal_event_data'),

    path('api/completed-events/', views.get_completed_events, name='api_completed_events'),
    path('api/compare-events/', views.compare_events, name='api_compare_events'),
    path('api/event-details/<int:event_id>/', views.get_event_details, name='api_event_details'),
    path('api/event-statistics/<int:event_id>/', views.get_event_statistics, name='api_event_statistics'),
    path('api/event-data/<int:id>/', views.cal_event_data, name='cal_event_data'),


    path('update-user/', views.update_user, name='update_user'),
    path('update-user-form/', views.update_user_form, name='update_user_form'),
    
    



    

    
]