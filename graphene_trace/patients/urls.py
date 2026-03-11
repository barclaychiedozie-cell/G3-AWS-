from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("comments/", views.comments, name="comments"),

    # Live (DB PressureData)
    path("api/live-grid/", views.live_grid_json, name="live_grid_json"),
    path("api/live-heatmap-chart/", views.live_heatmap_chart_json, name="live_heatmap_chart_json"),
    path("api/pressure-history/", views.pressure_history_json, name="pressure_history_json"),

    # Past (CSV files via PressureUpload)
    path("api/past-days/", views.past_days_json, name="past_days_json"),
    path("api/past-day-grid/", views.past_day_grid_json, name="past_day_grid_json"),
]