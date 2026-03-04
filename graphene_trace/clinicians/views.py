from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from patients.models import Comment
from patients.forms import CommentForm

User = get_user_model()


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