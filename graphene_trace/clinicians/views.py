from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from patients.forms import CommentForm
from patients.models import Comment

User = get_user_model()


@login_required
def dashboard(request):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    query = (request.GET.get("q") or "").strip()
    patients = User.objects.filter(role="patient").order_by("-high_priority", "username")

    if query:
        patients = patients.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(id_number__icontains=query)
        )

    return render(
        request,
        "clinicians/dashboard.html",
        {
            "patients": patients[:50],
            "query": query,
        },
    )


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
def toggle_priority(request, patient_id):
    if request.user.role != "clinician":
        return render(request, "403.html", status=403)

    patient = get_object_or_404(User, id=patient_id, role="patient")
    patient.high_priority = not patient.high_priority
    patient.save(update_fields=["high_priority"])

    return redirect("clinician_dashboard")
