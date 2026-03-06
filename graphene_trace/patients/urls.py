from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("comments/", views.comments, name="comments"),
    path("api/live-grid/", views.live_grid_json, name="live_grid_json"),
    path("api/live-heatmap-chart/", views.live_heatmap_chart_json, name="live_heatmap_chart_json"),
]