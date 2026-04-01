from django.urls import path
from . import views

urlpatterns = [
    path("clinician/dashboard/", views.dashboard, name="clinician_dashboard"),
    path("clinician/patient/<int:patient_id>/comments/", views.patient_comments, name="patient_comments"),
    path("clinician/patient/<int:patient_id>/priority/", views.toggle_priority, name="toggle_priority"),
]
