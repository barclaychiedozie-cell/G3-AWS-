from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="clinician_dashboard"),
    path("patient/<int:patient_id>/comments/", views.patient_comments, name="patient_comments"),
    path("patient/<int:patient_id>/priority/", views.toggle_priority, name="toggle_priority"),
    path("patient/<int:patient_id>/graph/", views.patient_pressure_graph, name="patient_pressure_graph"),
    path("patient/<int:patient_id>/flags/", views.flagged_periods, name="flagged_periods"),
]