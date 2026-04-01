import csv
import math
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


def _connected_components(active_mask):
    rows = len(active_mask)
    visited = set()
    sizes = []

    for r in range(rows):
        for c in range(len(active_mask[r])):
            if not active_mask[r][c] or (r, c) in visited:
                continue
            stack = [(r, c)]
            visited.add((r, c))
            size = 0
            while stack:
                cr, cc = stack.pop()
                size += 1
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if nr < 0 or nr >= rows:
                        continue
                    if nc < 0 or nc >= len(active_mask[nr]):
                        continue
                    if not active_mask[nr][nc] or (nr, nc) in visited:
                        continue
                    visited.add((nr, nc))
                    stack.append((nr, nc))
            sizes.append(size)
    return sizes


def _largest_active_peak(matrix):
    if not matrix:
        return 0.0

    active_mask = []
    for row in matrix:
        active_mask.append([value >= ACTIVE_THRESHOLD for value in row])

    component_sizes = _connected_components(active_mask)
    if not component_sizes or max(component_sizes) < 10:
        return 0.0

    return max(_flatten(matrix), default=0.0)


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


def _build_session_summary(upload):
    matrix = _read_upload_matrix(upload)
    score = _pressure_score(matrix)
    peak = round(_largest_active_peak(matrix), 2)
    contact_area = _contact_area_percent(matrix)
    avg_active = _avg_active_pressure(matrix)

    if score >= 75:
        plain_english = "You had a high pressure reading in your last session. A small posture change or weight shift may help reduce risk."
    elif score >= 45:
        plain_english = "Your last session showed some moderate pressure. Try changing position regularly to keep pressure spread out."
    else:
        plain_english = "Your last session looked well distributed with low pressure overall."

    return {
        "upload_id": upload.id,
        "timestamp": upload.timestamp.isoformat(),
        "pressure_score": score,
        "pressure_label": _pressure_label(score),
        "peak_pressure_index": peak,
        "contact_area_percent": contact_area,
        "average_active_pressure": avg_active,
        "plain_english": plain_english,
    }


@login_required
def dashboard(request):
    if request.user.role != "patient":
        return render(request, "403.html", status=403)

    notifications = Notification.objects.filter(patient=request.user).order_by("-timestamp")[:10]
    latest_upload = PressureUpload.objects.filter(patient=request.user).order_by("-timestamp").first()
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
        match = SENSOR_RE.match((row.sensor_location or "").strip())
        if not match:
            continue
        cells.append({"r": int(match.group(1)), "c": int(match.group(2)), "value": float(row.pressure_value or 0)})
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
        ts = row["timestamp"].isoformat()
        value = float(row["pressure_value"] or 0)
        bucket = buckets.get(ts)
        if not bucket:
            bucket = {"timestamp": ts, "sum": 0.0, "count": 0, "max": value}
            buckets[ts] = bucket
        bucket["sum"] += value
        bucket["count"] += 1
        if value > bucket["max"]:
            bucket["max"] = value

    data = []
    for bucket in sorted(buckets.values(), key=lambda item: item["timestamp"]):
        data.append({"timestamp": bucket["timestamp"], "max": bucket["max"], "avg": (bucket["sum"] / bucket["count"]) if bucket["count"] else 0})
    return JsonResponse({"data": data})


@login_required
def comments(request):
    if request.user.role != "patient":
        return render(request, "403.html", status=403)

    if request.method == "POST":
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.patient = request.user
            comment.save()
            return redirect("comments")
    else:
        form = CommentForm(user=request.user)

    comments_qs = Comment.objects.filter(patient=request.user).order_by("-timestamp")
    return render(request, "patients/comments.html", {"form": form, "comments": comments_qs})


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

    data = []
    for row in reversed(list(qs)):
        data.append(
            {
                "timestamp": row["timestamp"].isoformat(),
                "sensor_location": row["sensor_location"],
                "pressure_value": float(row["pressure_value"] or 0),
            }
        )
    return JsonResponse({"data": data})


@login_required
def past_days_json(request):
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    limit_days = int(request.GET.get("limit", "30"))
    limit_days = max(1, min(limit_days, 366))
    uploads = PressureUpload.objects.filter(patient=request.user).order_by("-timestamp")

    day_map = {}
    for upload in uploads:
        day_str = timezone.localtime(upload.timestamp).date().isoformat()
        if day_str not in day_map:
            day_map[day_str] = upload
        if len(day_map) >= limit_days:
            break

    data = []
    for day, upload in sorted(day_map.items(), key=lambda item: item[0], reverse=True):
        data.append(
            {
                "day": day,
                "upload_id": upload.id,
                "timestamp": upload.timestamp.isoformat(),
                "uploaded_at": upload.uploaded_at.isoformat(),
                "rows": upload.rows,
                "cols": upload.cols,
            }
        )
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
        PressureUpload.objects.filter(patient=request.user, timestamp__gte=start_local, timestamp__lt=end_local)
        .order_by("-timestamp")
        .first()
    )
    if not upload:
        return JsonResponse({"error": "not found"}, status=404)

    full_matrix = _read_upload_matrix(upload)
    source_rows = len(full_matrix)
    source_cols = max((len(r) for r in full_matrix), default=0)

    if source_rows == 0 or source_cols == 0:
        return JsonResponse(
            {
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
            }
        )

    row_step = max(1, math.ceil(source_rows / max_rows))
    col_step = max(1, math.ceil(source_cols / max_cols))

    matrix = []
    for r in range(0, source_rows, row_step):
        src = full_matrix[r]
        ds_row = []
        for c in range(0, source_cols, col_step):
            ds_row.append(src[c] if c < len(src) else 0.0)
        matrix.append(ds_row)

    return JsonResponse(
        {
            "day": day.isoformat(),
            "upload_id": upload.id,
            "timestamp": upload.timestamp.isoformat(),
            "rows": len(matrix),
            "cols": max((len(r) for r in matrix), default=0),
            "matrix": matrix,
            "downsampled": (row_step > 1 or col_step > 1),
            "source_rows": source_rows,
            "source_cols": source_cols,
            "row_step": row_step,
            "col_step": col_step,
        }
    )


@login_required
def last_session_summary_json(request):
    if request.user.role != "patient":
        return JsonResponse({"error": "forbidden"}, status=403)

    latest_upload = PressureUpload.objects.filter(patient=request.user).order_by("-timestamp").first()
    if not latest_upload:
        return JsonResponse({"error": "no sessions found"}, status=404)

    return JsonResponse(_build_session_summary(latest_upload))
