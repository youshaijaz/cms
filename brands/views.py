from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BrandForm
from .models import Brand


@login_required
def brand_list(request):
    brands = Brand.objects.filter(owner=request.user)

    return render(
        request,
        "brands/brand_list.html",
        {"brands": brands},
    )


@login_required
def brand_create(request):
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)

        if form.is_valid():
            brand = form.save(commit=False)
            brand.owner = request.user
            brand.save()

            messages.success(request, "Brand created successfully.")
            return redirect("brands:detail", pk=brand.pk)
    else:
        form = BrandForm()

    return render(
        request,
        "brands/brand_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def brand_edit(request, pk):
    brand = get_object_or_404(
        Brand,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = BrandForm(
            request.POST,
            request.FILES,
            instance=brand,
        )

        if form.is_valid():
            form.save()

            messages.success(request, "Brand updated successfully.")
            return redirect("brands:detail", pk=brand.pk)
    else:
        form = BrandForm(instance=brand)

    return render(
        request,
        "brands/brand_form.html",
        {
            "form": form,
            "brand": brand,
            "is_edit": True,
        },
    )


@login_required
def brand_detail(request, pk):
    brand = get_object_or_404(
        Brand,
        pk=pk,
        owner=request.user,
    )

    return render(
        request,
        "brands/brand_detail.html",
        {"brand": brand},
    )