import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import CommentForm
from .models import Comment, Notification, PressureData

User = get_user_model()


@login_required
def dashboard(request):
    if request.user.role != "patient":
        return render(request, "403.html")

    if request.method == "POST":
        feedback_text = (request.POST.get("feedback_text") or "").strip()
        clinician_id_raw = request.POST.get("clinician_id")

        target_clinician = None
        try:
            target_clinician = User.objects.get(id=int(clinician_id_raw), role="clinician")
        except (TypeError, ValueError, User.DoesNotExist):
            target_clinician = None

        if feedback_text:
            Comment.objects.create(
                patient=request.user,
                clinician=target_clinician,
                text=feedback_text,
                # In feedback threads, patient messages are "not reply" and clinician messages are reply.
                is_reply=False,
            )
            if target_clinician:
                return redirect(f"/patient/dashboard/?thread_clinician_id={target_clinician.id}")
            return redirect("patient_dashboard")

    # Latest notifications on the dashboard (most recent first)
    notifications = (
        Notification.objects.filter(patient=request.user)
        .order_by("-timestamp")[:10]
    )

    clinicians = (
        User.objects.filter(
            role="clinician",
            clinician_comments__patient=request.user,
        )
        .distinct()
        .order_by("username")
    )
    if not clinicians.exists():
        clinicians = User.objects.filter(role="clinician").order_by("username")

    selected_clinician_id = request.GET.get("thread_clinician_id")
    selected_clinician = None
    if selected_clinician_id:
        try:
            selected_clinician = clinicians.get(id=int(selected_clinician_id))
        except (TypeError, ValueError, User.DoesNotExist):
            selected_clinician = None
    if not selected_clinician:
        selected_clinician = clinicians.first()

    feedback_messages = Comment.objects.none()
    if selected_clinician:
        feedback_messages = (
            Comment.objects.filter(
                patient=request.user,
                clinician=selected_clinician,
            )
            .select_related("patient", "clinician")
            .order_by("timestamp")
        )

    unread_notifications_count = Notification.objects.filter(
        patient=request.user,
        is_read=False,
    ).count()

    return render(
        request,
        "patients/dashboard.html",
        {
            "notifications": notifications,
            "feedback_messages": feedback_messages,
            "clinicians": clinicians,
            "selected_clinician": selected_clinician,
            "unread_notifications_count": unread_notifications_count,
        },
    )


@login_required
def live_grid_json(request):
    """
    Returns latest heatmap grid snapshot:
      { cells: [{r,c,value}, ...], timestamp: <iso> }

    Assumes PressureData.sensor_location like: r3_c7
    """
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    latest_ts = (
        PressureData.objects.filter(patient=request.user)
        .order_by("-timestamp")
        .values_list("timestamp", flat=True)
        .first()
    )
    if not latest_ts:
        return JsonResponse({"cells": [], "timestamp": None})

    rows = PressureData.objects.filter(patient=request.user, timestamp=latest_ts)

    cells = []
    for row in rows:
        m = re.match(r"r(\d+)_c(\d+)", (row.sensor_location or "").strip())
        if not m:
            continue
        cells.append(
            {
                "r": int(m.group(1)),
                "c": int(m.group(2)),
                "value": float(row.pressure_value or 0),
            }
        )

    return JsonResponse({"cells": cells, "timestamp": latest_ts.isoformat()})


@login_required
def live_heatmap_chart_json(request):
    """
    Real-time chart data derived from recent grid snapshots.
    Returns max & avg per timestamp within last 15 minutes:
      { data: [{timestamp, max, avg}, ...] }
    """
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    since = timezone.now() - timedelta(minutes=15)

    qs = (
        PressureData.objects.filter(patient=request.user, timestamp__gte=since)
        .values("timestamp", "pressure_value")
        .order_by("timestamp")
    )

    buckets = {}  # ts_iso -> {"timestamp":..., "sum":..., "count":..., "max":...}
    for row in qs:
        ts = row["timestamp"]
        ts_key = ts.isoformat()
        val = float(row["pressure_value"] or 0)

        b = buckets.get(ts_key)
        if not b:
            b = {"timestamp": ts_key, "sum": 0.0, "count": 0, "max": val}
            buckets[ts_key] = b

        b["sum"] += val
        b["count"] += 1
        if val > b["max"]:
            b["max"] = val

    data = sorted(buckets.values(), key=lambda x: x["timestamp"])
    out = [
        {
            "timestamp": d["timestamp"],
            "max": d["max"],
            "avg": (d["sum"] / d["count"]) if d["count"] else 0,
        }
        for d in data
    ]

    return JsonResponse({"data": out})


@login_required
def comments(request):
    if request.user.role != "patient":
        return render(request, "403.html")

    if request.method == "POST":
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            c = form.save(commit=False)
            c.patient = request.user
            c.save()
            return redirect("comments")
    else:
        form = CommentForm(user=request.user)

    comments_qs = Comment.objects.filter(patient=request.user).order_by("-timestamp")
    return render(request, "patients/comments.html", {"form": form, "comments": comments_qs})

@login_required
def pressure_history_json(request):
    """
    Historical pressure readings for the logged-in patient (CSV-uploaded or live).

    Optional query params:
      - since_minutes=1440 (default 1440 = last 24h)
      - limit=20000
    """
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    since_minutes = int(request.GET.get("since_minutes", "1440"))
    since_minutes = max(1, min(since_minutes, 60 * 24 * 365))

    limit = int(request.GET.get("limit", "20000"))
    limit = max(1, min(limit, 50000))

    since = timezone.now() - timedelta(minutes=since_minutes)

    qs = (
        PressureData.objects.filter(patient=request.user, timestamp__gte=since)
        .values("timestamp", "sensor_location", "pressure_value")
        .order_by("-timestamp")[:limit]
    )

    data = [
        {
            "timestamp": row["timestamp"].isoformat(),
            "sensor_location": row["sensor_location"],
            "pressure_value": float(row["pressure_value"] or 0),
        }
        for row in reversed(list(qs))
    ]

    return JsonResponse({"data": data})