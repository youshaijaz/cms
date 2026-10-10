from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BrandForm
from .models import Brand

from io import BytesIO

from django.http import Http404, HttpResponse
from PIL import Image, ImageOps


@login_required
def brand_logo(request, pk):
    brand = get_object_or_404(
        Brand,
        pk=pk,
        owner=request.user,
    )

    if not brand.logo:
        raise Http404("Logo not found.")

    output = BytesIO()

    try:
        with brand.logo.open("rb") as source:
            with Image.open(source) as image:
                logo = ImageOps.exif_transpose(image).convert("RGBA")
                logo.thumbnail((512, 512))
                logo.save(output, format="PNG")
    except FileNotFoundError:
        raise Http404("Logo not found.")

    response = HttpResponse(
        output.getvalue(),
        content_type="image/png",
    )
    response["Cache-Control"] = "private, no-store"
    return response



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