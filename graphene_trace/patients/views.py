import re
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import PressureData, Comment
from .forms import CommentForm


@login_required
def dashboard(request):
    if request.user.role != "patient":
        return render(request, "403.html")

    return render(request, "patients/dashboard.html")


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
        m = re.match(r"r(\d+)_c(\d+)", (row.sensor_location or "").strip())
        if not m:
            continue
        r = int(m.group(1))
        c = int(m.group(2))
        cells.append({"r": r, "c": c, "value": row.pressure_value})

    return JsonResponse({"cells": cells, "timestamp": latest_ts.isoformat()})
# ADD this function into the same patients/views.py

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