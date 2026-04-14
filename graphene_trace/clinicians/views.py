from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Max

from patients.models import (
    Comment,
    ClinicianPatientAccess,
    PressureData,
    HighPressureFlag,
)
from patients.forms import CommentForm

User = get_user_model()


@login_required
def dashboard(request):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    query = (request.GET.get("q") or "").strip()
    alert_filter = (request.GET.get("alert") or "").strip()

    allowed_patient_ids = ClinicianPatientAccess.objects.filter(
        clinician=request.user
    ).values_list("patient_id", flat=True)

    patients = User.objects.filter(
        role="patient",
        id__in=allowed_patient_ids,
    )

    if query:
        patients = patients.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(id_number__icontains=query)
        )

    if alert_filter:
        patients = patients.filter(
            notifications__alert_level=alert_filter
        ).distinct()

    patients = patients.annotate(
        notification_count=Count("notifications"),
        latest_alert=Max("notifications__timestamp"),
    ).order_by("-high_priority", "-latest_alert", "username")

    patient_rows = []
    for patient in patients[:50]:
        has_critical = patient.notifications.filter(alert_level="critical").exists()
        has_warning = patient.notifications.filter(alert_level="warning").exists()

        if has_critical:
            notification_color = "red"
        elif has_warning:
            notification_color = "orange"
        else:
            notification_color = "blue"

        flag_count = patient.pressure_flags.count()

        patient_rows.append(
            {
                "patient": patient,
                "notification_count": patient.notification_count,
                "notification_color": notification_color,
                "flag_count": flag_count,
            }
        )

    return render(
        request,
        "clinicians/dashboard.html",
        {
            "patient_rows": patient_rows,
            "query": query,
            "alert_filter": alert_filter,
        },
    )


@login_required
def toggle_priority(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    patient = get_object_or_404(User, id=patient_id, role="patient")
    patient.high_priority = not patient.high_priority
    patient.save(update_fields=["high_priority"])

    return redirect("clinician_dashboard")


@login_required
def patient_comments(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

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
    return render(
        request,
        "clinicians/patient_comments.html",
        {
            "patient": patient,
            "comments": comments,
            "form": form,
        },
    )


@login_required
def patient_pressure_graph(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    has_access = ClinicianPatientAccess.objects.filter(
        clinician=request.user,
        patient_id=patient_id,
    ).exists()

    if not has_access:
        return render(request, "403.html", status=403)

    patient = get_object_or_404(User, id=patient_id, role="patient")
    readings = PressureData.objects.filter(patient=patient).order_by("timestamp")[:500]

    labels = [r.timestamp.strftime("%Y-%m-%d %H:%M") for r in readings]
    values = [float(r.pressure_value or 0) for r in readings]

    return render(
        request,
        "clinicians/patient_pressure_graph.html",
        {
            "patient": patient,
            "labels": labels,
            "values": values,
        },
    )


@login_required
def flagged_periods(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    has_access = ClinicianPatientAccess.objects.filter(
        clinician=request.user,
        patient_id=patient_id,
    ).exists()

    if not has_access:
        return render(request, "403.html", status=403)

    patient = get_object_or_404(User, id=patient_id, role="patient")
    flags = HighPressureFlag.objects.filter(patient=patient).order_by("-start_time")

    return render(
        request,
        "clinicians/flagged_periods.html",
        {
            "patient": patient,
            "flags": flags,
        },
    )