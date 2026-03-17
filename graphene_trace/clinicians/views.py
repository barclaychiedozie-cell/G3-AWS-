from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone

from patients.models import Comment, Notification, PressureData
from patients.forms import CommentForm

User = get_user_model()


@login_required
def dashboard(request):
    if request.user.role != "clinician":
        return render(request, "403.html")

    patients = User.objects.filter(role="patient").order_by("username")

    if request.method == "POST":
        text = (request.POST.get("message_text") or "").strip()
        patient_id_raw = request.POST.get("message_patient_id")

        target_patient = None
        try:
            target_patient = patients.get(id=int(patient_id_raw))
        except (TypeError, ValueError, User.DoesNotExist):
            target_patient = None

        if target_patient and text:
            Comment.objects.create(
                patient=target_patient,
                clinician=request.user,
                text=text,
                is_reply=True,
            )
            clinician_name = request.user.get_full_name().strip() or request.user.username
            Notification.objects.create(
                patient=target_patient,
                message=f"New message from {clinician_name}: {text[:90]}",
                is_read=False,
            )
            return redirect(f"/clinician/dashboard/?thread_patient_id={target_patient.id}")

    selected_patient_id = request.GET.get("thread_patient_id")
    selected_patient = None
    if selected_patient_id:
        try:
            selected_patient = patients.get(id=int(selected_patient_id))
        except (TypeError, ValueError, User.DoesNotExist):
            selected_patient = None
    if not selected_patient:
        selected_patient = patients.first()

    thread_messages = Comment.objects.none()
    if selected_patient:
        thread_messages = (
            Comment.objects.filter(patient=selected_patient)
            .select_related("patient", "clinician")
            .order_by("timestamp")
        )

    return render(
        request,
        "clinician/dashboard.html",
        {
            "patients": patients,
            "selected_patient": selected_patient,
            "thread_messages": thread_messages,
        },
    )


@login_required
def comparison_report_json(request):
    if request.user.role != "clinician":
        return JsonResponse({"error": "forbidden"}, status=403)

    since_minutes = int(request.GET.get("since_minutes", "1440"))
    since_minutes = max(60, min(since_minutes, 60 * 24 * 30))
    since = timezone.now() - timedelta(minutes=since_minutes)

    raw_patient_ids = request.GET.getlist("patient_ids")
    patient_ids = []
    for value in raw_patient_ids:
        try:
            patient_ids.append(int(value))
        except (TypeError, ValueError):
            continue

    patient_qs = User.objects.filter(role="patient").order_by("username")
    if patient_ids:
        patient_qs = patient_qs.filter(id__in=patient_ids)
    patient_qs = patient_qs[:5]

    selected_patients = list(patient_qs)
    if not selected_patients:
        return JsonResponse({"labels": [], "datasets": []})

    selected_ids = [p.id for p in selected_patients]
    selected_names = {
        p.id: (p.get_full_name().strip() or p.username) for p in selected_patients
    }

    qs = (
        PressureData.objects.filter(patient_id__in=selected_ids, timestamp__gte=since)
        .values("patient_id", "timestamp", "pressure_value")
        .order_by("timestamp")
    )

    buckets = {}
    labels_set = set()
    for row in qs:
        ts = row["timestamp"].replace(minute=0, second=0, microsecond=0)
        ts_key = ts.isoformat()
        key = (row["patient_id"], ts_key)

        labels_set.add(ts_key)
        current = buckets.get(key)
        if not current:
            buckets[key] = {"sum": 0.0, "count": 0}
            current = buckets[key]

        current["sum"] += float(row["pressure_value"] or 0)
        current["count"] += 1

    labels = sorted(labels_set)
    datasets = []
    for pid in selected_ids:
        data = []
        for ts_key in labels:
            bucket = buckets.get((pid, ts_key))
            if not bucket or not bucket["count"]:
                data.append(None)
            else:
                data.append(bucket["sum"] / bucket["count"])

        datasets.append(
            {
                "patient_id": pid,
                "label": selected_names.get(pid, f"Patient {pid}"),
                "data": data,
            }
        )

    return JsonResponse({"labels": labels, "datasets": datasets})


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