from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    path("reports/", views.report_list, name="report_list"),
    path("reports/new/", views.create_report, name="create_report"),
    path("reports/<int:pk>/", views.certificate_view, name="certificate_detail"),
    path("reports/<int:pk>/edit/", views.edit_report, name="edit_report"),
    path("reports/<int:pk>/delete/", views.delete_report, name="delete_report"),
    
    path("procedures/", views.procedure_list, name="procedure_list"),
    path("procedures/new/", views.create_procedure, name="create_procedure"),
    path("procedures/<int:pk>/edit/", views.edit_procedure, name="edit_procedure"),
    
    path("profile/", views.profile_view, name="profile"),
    path("api/check-report-number/", views.check_report_number, name="check_report_number"),
]
