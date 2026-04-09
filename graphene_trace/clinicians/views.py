import csv
from datetime import datetime, timedelta
from io import TextIOWrapper

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_date

from patients.models import Comment, Message, PressureData, PressureUpload
from patients.forms import CommentForm

User = get_user_model()


def _open_csv_text(fh):
    """
    Robust CSV decoding for Excel/Windows exports.
    """
    try:
        return TextIOWrapper(fh, encoding="utf-8-sig", errors="replace", newline="")
    except Exception:
        return TextIOWrapper(fh, encoding="cp1252", errors="replace", newline="")


def _upload_metric(upload, metric):
    total = 0.0
    count = 0
    max_val = None

    with upload.csv_file.open("rb") as fh:
        wrapper = _open_csv_text(fh)
        reader = csv.reader(wrapper)
        for row in reader:
            if not row:
                continue
            for cell in row:
                raw = (cell or "").strip()
                if raw == "":
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    continue
                total += value
                count += 1
                if max_val is None or value > max_val:
                    max_val = value

    if not count:
        return 0.0
    if metric == "max":
        return max_val or 0.0
    return total / count


def _upload_stats(upload):
    total_cells = 0
    active_cells = 0
    max_val = None

    with upload.csv_file.open("rb") as fh:
        wrapper = _open_csv_text(fh)
        reader = csv.reader(wrapper)
        for row in reader:
            if not row:
                continue
            for cell in row:
                raw = (cell or "").strip()
                if raw == "":
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    continue
                total_cells += 1
                if value > 0:
                    active_cells += 1
                if max_val is None or value > max_val:
                    max_val = value

    if not total_cells:
        return {
            "max_value": 0.0,
            "contact_area_pct": 0.0,
        }

    return {
        "max_value": max_val or 0.0,
        "contact_area_pct": (active_cells / total_cells) * 100.0,
    }


@login_required
def dashboard(request):
    if request.user.role != "clinician":
        return render(request, "403.html")

    patients = list(User.objects.filter(role="patient").order_by("username"))

    unread_by_sender = {
        row["sender_id"]: row["count"]
        for row in Message.objects.filter(receiver=request.user, is_read=False)
        .values("sender_id")
        .annotate(count=Count("id"))
    }

    for patient in patients:
        patient.unread_count = unread_by_sender.get(patient.id, 0)

    unread_messages_total = sum(unread_by_sender.values())

    selected_patient_id = request.GET.get("thread_patient_id")
    selected_patient = None
    if selected_patient_id:
        try:
            selected_patient = next(
                p for p in patients if p.id == int(selected_patient_id)
            )
        except (TypeError, ValueError, StopIteration):
            selected_patient = None
    if not selected_patient:
        selected_patient = patients[0] if patients else None

    chat_messages = []
    last_chat_message_id = 0
    peak_pressure_index = None
    contact_area_pct = None
    risk_level = None
    if selected_patient:
        latest_upload = (
            PressureUpload.objects.filter(patient=selected_patient)
            .order_by("-timestamp")
            .first()
        )
        if latest_upload:
            stats = _upload_stats(latest_upload)
            peak_pressure_index = stats["max_value"]
            contact_area_pct = stats["contact_area_pct"]
            if peak_pressure_index < 50:
                risk_level = "Low"
            elif peak_pressure_index < 100:
                risk_level = "Moderate"
            else:
                risk_level = "High"

        chat_qs = (
            Message.objects.filter(
                Q(sender=request.user, receiver=selected_patient)
                | Q(sender=selected_patient, receiver=request.user)
            )
            .select_related("sender", "receiver")
            .order_by("-timestamp")[:30]
        )
        chat_messages = list(reversed(chat_qs))
        if chat_messages:
            last_chat_message_id = chat_messages[-1].id

    return render(
        request,
        "clinician/dashboard.html",
        {
            "patients": patients,
            "selected_patient": selected_patient,
            "chat_messages": chat_messages,
            "last_chat_message_id": last_chat_message_id,
            "chat_other_user": selected_patient,
            "unread_messages_total": unread_messages_total,
            "peak_pressure_index": peak_pressure_index,
            "contact_area_pct": contact_area_pct,
            "risk_level": risk_level,
        },
    )


@login_required
def comparison_report_json(request):
    if request.user.role != "clinician":
        return JsonResponse({"error": "forbidden"}, status=403)

    patient_id_raw = request.GET.get("patient_id")
    source = (request.GET.get("source") or "both").strip().lower()
    metric = (request.GET.get("metric") or "avg").strip().lower()
    start_raw = (request.GET.get("start_date") or "").strip()
    end_raw = (request.GET.get("end_date") or "").strip()

    if metric not in {"avg", "max"}:
        metric = "avg"
    if source not in {"live", "uploads", "both"}:
        source = "both"
    patient = None
    if patient_id_raw:
        try:
            patient = User.objects.get(id=int(patient_id_raw), role="patient")
        except (TypeError, ValueError, User.DoesNotExist):
            patient = None

    if not patient:
        patient = User.objects.filter(role="patient").order_by("username").first()

    if not patient:
        return JsonResponse({"labels": [], "datasets": []})

    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None

    tz = timezone.get_current_timezone()
    start_local = None
    end_local = None
    if start_date:
        start_local = timezone.make_aware(
            datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0),
            tz,
        )
    if end_date:
        end_local = timezone.make_aware(
            datetime(end_date.year, end_date.month, end_date.day, 0, 0, 0),
            tz,
        ) + timedelta(days=1)

    live_buckets = {}
    upload_buckets = {}

    if source in {"live", "both"}:
        qs = PressureData.objects.filter(patient=patient)
        if start_local:
            qs = qs.filter(timestamp__gte=start_local)
        if end_local:
            qs = qs.filter(timestamp__lt=end_local)
        qs = qs.values("timestamp", "pressure_value").order_by("timestamp")

        for row in qs:
            day = timezone.localtime(row["timestamp"]).date().isoformat()
            value = float(row["pressure_value"] or 0)
            bucket = live_buckets.get(day)
            if not bucket:
                bucket = {"sum": 0.0, "count": 0, "max": value}
                live_buckets[day] = bucket
            bucket["sum"] += value
            bucket["count"] += 1
            if value > bucket["max"]:
                bucket["max"] = value

    if source in {"uploads", "both"}:
        uploads = PressureUpload.objects.filter(patient=patient)
        if start_local:
            uploads = uploads.filter(timestamp__gte=start_local)
        if end_local:
            uploads = uploads.filter(timestamp__lt=end_local)
        uploads = uploads.order_by("timestamp")

        for upload in uploads:
            day = timezone.localtime(upload.timestamp).date().isoformat()
            value = _upload_metric(upload, metric)
            bucket = upload_buckets.get(day)
            if not bucket:
                bucket = {"sum": 0.0, "count": 0, "max": value}
                upload_buckets[day] = bucket
            bucket["sum"] += value
            bucket["count"] += 1
            if value > bucket["max"]:
                bucket["max"] = value

    labels = sorted(set(live_buckets.keys()) | set(upload_buckets.keys()))

    def build_series(buckets):
        if metric == "max":
            return [buckets.get(day, {}).get("max") for day in labels]
        return [
            (buckets[day]["sum"] / buckets[day]["count"]) if day in buckets and buckets[day]["count"] else None
            for day in labels
        ]

    datasets = []
    display_name = patient.get_full_name().strip() or patient.username
    if source in {"live", "both"}:
        datasets.append(
            {
                "patient_id": patient.id,
                "label": f"{display_name} (Live)",
                "data": build_series(live_buckets),
                "color": "#3b82f6",
            }
        )
    if source in {"uploads", "both"}:
        datasets.append(
            {
                "patient_id": patient.id,
                "label": f"{display_name} (Uploads)",
                "data": build_series(upload_buckets),
                "color": "#22c55e",
            }
        )

    return JsonResponse(
        {
            "labels": labels,
            "datasets": datasets,
        }
    )


@login_required
def patient_comments(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html")

    patient = get_object_or_404(User, id=patient_id, role="patient")

    if request.method == "POST":
        form = CommentForm(request.POST, user=patient)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.patient = patient
            reply.clinician = request.user
            reply.is_reply = True
            reply.save()
            return redirect("patient_comments", patient_id=patient_id)
    else:
        form = CommentForm(user=patient)

    comments = Comment.objects.filter(patient=patient).order_by("-timestamp")
    return render(request, "clinicians/patient_comments.html", {"patient": patient, "comments": comments, "form": form})