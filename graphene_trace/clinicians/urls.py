from django.urls import path
from . import views

urlpatterns = [
    path("clinician/dashboard/", views.dashboard, name="clinician_dashboard"),
    path(
        "clinician/api/comparison-report/",
        views.comparison_report_json,
        name="clinician_comparison_report_json",
    ),
    path("patient/<int:patient_id>/comments/", views.patient_comments, name="patient_comments"),
]