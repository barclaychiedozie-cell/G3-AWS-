from django.urls import path
from . import views

urlpatterns = [
    path("patient/<int:patient_id>/comments/", views.patient_comments, name="patient_comments"),
]