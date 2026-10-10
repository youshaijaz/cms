import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from brands.models import Brand
from .forms import PostForm
from .models import Post
from .services.ai_service import suggest_caption
from .services.image_service import ImageRenderError, render_post
from contextlib import ExitStack
from types import SimpleNamespace

from .models import PostPhoto, PostTemplate
from .services.template_catalog import TEMPLATES
from uuid import uuid4

logger = logging.getLogger(__name__)


def owned_post(request, pk):
    return get_object_or_404(
        Post.objects.select_related("brand", "template"),
        pk=pk,
        brand__owner=request.user,
    )


@login_required
def template_cards():
    templates = PostTemplate.objects.filter(
        is_active=True,
        layout__in=TEMPLATES,
    ).order_by("name")

    return [
        {
            "template": template,
            "photo_count": len(TEMPLATES[template.layout]["slots"]),
        }
        for template in templates
    ]


def save_post_design(form):
    post = form.save(commit=False)
    spec = TEMPLATES[post.template.layout]
    photo_count = len(spec["slots"])

    old_image_name = post.image.name if post.pk else ""
    new_files = []
    replaced_files = []

    try:
        with ExitStack() as stack:
            sources = []

            for position in range(1, photo_count + 1):
                uploaded = form.cleaned_data.get(f"photo_{position}")

                if uploaded:
                    sources.append(uploaded)
                else:
                    existing = form.existing_photos[position]
                    sources.append(
                        stack.enter_context(existing.image.open("rb"))
                    )

            rendered = render_post(
                post.template,
                post.brand,
                post.headline,
                post.body_text,
                photos=sources,
                background_color=post.background_color,
                text_color=post.text_color,
            )

        caption_data = suggest_caption(
            post.brand,
            post.headline,
            post.body_text,
        )
        post.caption = caption_data["caption"]
        post.hashtags = caption_data["hashtags"]

        try:
            post.image.save(rendered.name, rendered, save=False)
            new_files.append((post.image.storage, post.image.name))
        finally:
            rendered.close()

        with transaction.atomic():
            post.save()

            for position in range(1, photo_count + 1):
                uploaded = form.cleaned_data.get(f"photo_{position}")

                if not uploaded:
                    continue

                photo = form.existing_photos.get(position)

                if photo is None:
                    photo = PostPhoto(post=post, position=position)
                elif photo.image:
                    replaced_files.append(
                        (photo.image.storage, photo.image.name)
                    )

                uploaded.seek(0)
                photo.image.save(
                    f"{uuid4().hex}.png",
                    uploaded,
                    save=False,
                )
                new_files.append((photo.image.storage, photo.image.name))
                photo.save()

            # Remove unused photo slots if a smaller layout was chosen.
            for photo in post.photos.filter(position__gt=photo_count):
                replaced_files.append(
                    (photo.image.storage, photo.image.name)
                )
                photo.delete()

    except Exception:
        for storage, name in new_files:
            storage.delete(name)
        raise

    if old_image_name:
        replaced_files.append((post.image.storage, old_image_name))

    # Cleanup failure shouldn't make a successful generation look failed.
    for storage, name in replaced_files:
        try:
            storage.delete(name)
        except Exception:
            logger.warning("Could not remove a replaced image.")

    return post, caption_data["used_ai"]


@login_required
def post_create(request):
    return post_editor(request)


@login_required
def post_edit(request, pk):
    post = owned_post(request, pk)
    return post_editor(request, instance=post)


def post_editor(request, instance=None):
    if not Brand.objects.filter(owner=request.user).exists():
        messages.info(request, "Create a brand first.")
        return redirect("brands:create")

    initial = {}

    if instance is None and request.GET.get("brand"):
        brand = get_object_or_404(
            Brand,
            pk=request.GET["brand"],
            owner=request.user,
        )
        initial["brand"] = brand

    form = PostForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        user=request.user,
        instance=instance,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        try:
            post, used_ai = save_post_design(form)
        except ImageRenderError as error:
            form.add_error(None, str(error))
        except Exception:
            logger.exception("Photo post generation failed")
            form.add_error(
                None,
                "We couldn't save this design. Please try again.",
            )
        else:
            messages.success(request, "Your design is ready.")

            if not used_ai:
                messages.info(request, "A basic caption was used.")

            return redirect("posts:detail", pk=post.pk)

    return render(
        request,
        "posts/post_form.html",
        {
            "form": form,
            "template_cards": template_cards(),
            "is_edit": instance is not None,
            "post": instance,
        },
    )


@login_required
def template_preview(request, pk):
    template = get_object_or_404(
        PostTemplate,
        pk=pk,
        is_active=True,
    )

    if template.layout not in TEMPLATES:
        raise Http404("Template not found.")

    sample_brand = SimpleNamespace(primary_color="#D4F66A")

    image = render_post(
        template,
        sample_brand,
        "Your next story.",
        "A little moment worth sharing.",
        preview=True,
    )

    try:
        response = HttpResponse(image.read(), content_type="image/png")
    finally:
        image.close()

    response["Cache-Control"] = "private, max-age=300"
    return response

@login_required
def post_detail(request, pk):
    post = owned_post(request, pk)

    return render(
        request,
        "posts/post_detail.html",
        {"post": post},
    )


@login_required
def post_image(request, pk):
    post = owned_post(request, pk)

    if not post.image:
        raise Http404("Image not found.")

    try:
        image_file = post.image.open("rb")
    except FileNotFoundError:
        raise Http404("Image not found.")

    response = FileResponse(
        image_file,
        content_type="image/png",
        as_attachment=request.GET.get("download") == "1",
        filename=f"post-{post.pk}.png",
    )
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
def post_caption_download(request, pk):
    post = owned_post(request, pk)

    response = HttpResponse(
        post.full_caption,
        content_type="text/plain; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="caption-{post.pk}.txt"'
    )
    response["Cache-Control"] = "private, no-store"
    return response