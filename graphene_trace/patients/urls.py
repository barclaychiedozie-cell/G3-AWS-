from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/live-grid/", views.live_grid_json, name="live_grid_json"),
    path("comments/", views.comments, name="comments"),
]