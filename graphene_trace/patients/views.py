import csv
import re
from datetime import datetime, timedelta
from io import TextIOWrapper

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import CommentForm
from .models import Comment, Notification, PressureData, PressureUpload


SENSOR_RE = re.compile(r"r(\d+)_c(\d+)$")
ACTIVE_THRESHOLD = 10.0


def _open_csv_text(fh):
    try:
        return TextIOWrapper(fh, encoding="utf-8-sig", errors="replace", newline="")
    except Exception:
        return TextIOWrapper(fh, encoding="cp1252", errors="replace", newline="")


def _read_upload_matrix(upload):
    matrix = []
    with upload.csv_file.open("rb") as fh:
        wrapper = _open_csv_text(fh)
        reader = csv.reader(wrapper)
        for row in reader:
            if not row:
                continue
            clean_row = []
            for cell in row:
                raw = (cell or "").strip()
                if raw == "":
                    clean_row.append(0.0)
                else:
                    try:
                        clean_row.append(float(raw))
                    except ValueError:
                        clean_row.append(0.0)
            matrix.append(clean_row)
    return matrix


def _flatten(matrix):
    return [value for row in matrix for value in row]


def _contact_area_percent(matrix):
    values = _flatten(matrix)
    if not values:
        return 0.0
    active = sum(1 for value in values if value >= ACTIVE_THRESHOLD)
    return round((active / len(values)) * 100.0, 2)


def _avg_active_pressure(matrix):
    active_values = [value for value in _flatten(matrix) if value >= ACTIVE_THRESHOLD]
    if not active_values:
        return 0.0
    return round(sum(active_values) / len(active_values), 2)


def _largest_active_peak(matrix):
    values = _flatten(matrix)
    if not values:
        return 0.0
    active_values = [v for v in values if v >= ACTIVE_THRESHOLD]
    return round(max(active_values), 2) if active_values else 0.0


def _pressure_score(matrix):
    peak = _largest_active_peak(matrix)
    if peak <= 0:
        return 0
    score = round((peak / 4095.0) * 100)
    return max(0, min(100, score))


def _pressure_label(score):
    if score >= 75:
        return "High pressure"
    if score >= 45:
        return "Moderate pressure"
    return "Low pressure"


def _build_patient_friendly_explanation(score):
    if score >= 75:
        return "Your seat pressure looks high. Try a small posture change or shift your weight to reduce pressure."
    if score >= 45:
        return "Your pressure is moderate. A small movement or position change may help spread pressure more evenly."
    return "Your pressure looks well spread out. Keep changing position regularly to stay comfortable."


def _build_session_summary(upload):
    matrix = _read_upload_matrix(upload)
    score = _pressure_score(matrix)
    peak = _largest_active_peak(matrix)
    contact_area = _contact_area_percent(matrix)
    avg_active = _avg_active_pressure(matrix)

    return {
        "upload_id": upload.id,
        "timestamp": upload.timestamp.isoformat(),
        "pressure_score": score,
        "pressure_label": _pressure_label(score),
        "peak_pressure_index": peak,
        "contact_area_percent": contact_area,
        "average_active_pressure": avg_active,
        "plain_english": _build_patient_friendly_explanation(score),
    }


@login_required
def dashboard(request):
    if request.user.role != "patient":
        return render(request, "403.html", status=403)

    notifications = (
        Notification.objects.filter(patient=request.user)
        .order_by("-timestamp")[:10]
    )

    latest_upload = (
        PressureUpload.objects.filter(patient=request.user)
        .order_by("-timestamp")
        .first()
    )

    session_summary = _build_session_summary(latest_upload) if latest_upload else None

    return render(
        request,
        "patients/dashboard.html",
        {
            "notifications": notifications,
            "session_summary": session_summary,
        },
    )


@login_required
def live_grid_json(request):
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
        m = SENSOR_RE.match((row.sensor_location or "").strip())
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
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    since = timezone.now() - timedelta(minutes=15)

    qs = (
        PressureData.objects.filter(patient=request.user, timestamp__gte=since)
        .values("timestamp", "pressure_value")
        .order_by("timestamp")
    )

    buckets = {}
    for row in qs:
        ts_key = row["timestamp"].isoformat()
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
        return render(request, "403.html", status=403)

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
    return render(
        request,
        "patients/comments.html",
        {"form": form, "comments": comments_qs},
    )


@login_required
def pressure_history_json(request):
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


@login_required
def past_days_json(request):
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    limit_days = int(request.GET.get("limit", "30"))
    limit_days = max(1, min(limit_days, 366))

    uploads = PressureUpload.objects.filter(patient=request.user).order_by("-timestamp")

    day_map = {}
    for u in uploads:
        day_str = timezone.localtime(u.timestamp).date().isoformat()
        if day_str not in day_map:
            day_map[day_str] = u
        if len(day_map) >= limit_days:
            break

    data = [
        {
            "day": day,
            "upload_id": u.id,
            "timestamp": u.timestamp.isoformat(),
            "uploaded_at": u.uploaded_at.isoformat(),
            "rows": u.rows,
            "cols": u.cols,
        }
        for day, u in sorted(day_map.items(), key=lambda x: x[0], reverse=True)
    ]
    return JsonResponse({"data": data})


@login_required
def past_day_grid_json(request):
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    day_raw = (request.GET.get("day") or "").strip()
    if not day_raw:
        return JsonResponse({"error": "missing day"}, status=400)

    day = parse_date(day_raw)
    if not day:
        return JsonResponse({"error": f"day not parseable: {day_raw}"}, status=400)

    max_rows = int(request.GET.get("max_rows", "60"))
    max_cols = int(request.GET.get("max_cols", "60"))
    max_rows = max(5, min(max_rows, 400))
    max_cols = max(5, min(max_cols, 400))

    tz = timezone.get_current_timezone()
    start_local = timezone.make_aware(datetime(day.year, day.month, day.day, 0, 0, 0), tz)
    end_local = start_local + timedelta(days=1)

    upload = (
        PressureUpload.objects.filter(
            patient=request.user,
            timestamp__gte=start_local,
            timestamp__lt=end_local,
        )
        .order_by("-timestamp")
        .first()
    )
    if not upload:
        return JsonResponse({"error": "not found"}, status=404)

    full_matrix = _read_upload_matrix(upload)
    source_rows = len(full_matrix)
    source_cols = max((len(r) for r in full_matrix), default=0)

    if source_rows == 0 or source_cols == 0:
        return JsonResponse({
            "day": day.isoformat(),
            "upload_id": upload.id,
            "timestamp": upload.timestamp.isoformat(),
            "rows": 0,
            "cols": 0,
            "matrix": [],
            "downsampled": False,
            "source_rows": 0,
            "source_cols": 0,
            "row_step": 1,
            "col_step": 1,
        })

    row_step = max(1, (source_rows + max_rows - 1) // max_rows)
    col_step = max(1, (source_cols + max_cols - 1) // max_cols)

    matrix = []
    for r in range(0, source_rows, row_step):
        src = full_matrix[r]
        ds_row = []
        for c in range(0, source_cols, col_step):
            ds_row.append(src[c] if c < len(src) else 0.0)
        matrix.append(ds_row)

    return JsonResponse({
        "day": day.isoformat(),
        "upload_id": upload.id,
        "timestamp": upload.timestamp.isoformat(),
        "rows": len(matrix),
        "cols": max(len(r) for r in matrix) if matrix else 0,
        "matrix": matrix,
        "downsampled": (row_step > 1 or col_step > 1),
        "source_rows": source_rows,
        "source_cols": source_cols,
        "row_step": row_step,
        "col_step": col_step,
    })