from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="patient_dashboard"),
    path("patient/dashboard/", views.dashboard, name="patient_dashboard_legacy"),
    path("comments/", views.comments, name="comments"),

    # Live (DB PressureData)
    path("api/live-grid/", views.live_grid_json, name="live_grid_json"),
    path("api/live-heatmap-chart/", views.live_heatmap_chart_json, name="live_heatmap_chart_json"),
    path("api/pressure-history/", views.pressure_history_json, name="pressure_history_json"),

    # Past (CSV files via PressureUpload)
    path("api/past-days/", views.past_days_json, name="past_days_json"),
    path("api/past-day-grid/", views.past_day_grid_json, name="past_day_grid_json"),

    # Messages (patient/clinician chat)
    path("messages/<int:user_id>/", views.message_thread_api, name="message_thread_api"),
    path("api/messages/", views.message_thread_api, name="message_thread_api_legacy"),
]