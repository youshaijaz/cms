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


logger = logging.getLogger(__name__)


def owned_post(request, pk):
    return get_object_or_404(
        Post.objects.select_related("brand", "template"),
        pk=pk,
        brand__owner=request.user,
    )


@login_required
def post_create(request):
    if not Brand.objects.filter(owner=request.user).exists():
        messages.info(request, "Create a brand before making a post.")
        return redirect("brands:create")

    initial = {}

    if request.method == "GET" and request.GET.get("brand"):
        brand = get_object_or_404(
            Brand,
            pk=request.GET["brand"],
            owner=request.user,
        )
        initial["brand"] = brand

    form = PostForm(
        request.POST if request.method == "POST" else None,
        user=request.user,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        image_file = None

        try:
            image_file = render_post(
                post.template,
                post.brand,
                post.headline,
                post.body_text,
            )

            caption_data = suggest_caption(
                post.brand,
                post.headline,
                post.body_text,
            )

            post.caption = caption_data["caption"]
            post.hashtags = caption_data["hashtags"]

            # File storage is outside the database transaction.
            post.image.save(
                image_file.name,
                image_file,
                save=False,
            )

            with transaction.atomic():
                post.save()

        except Exception as error:
            if post.image.name:
                post.image.storage.delete(post.image.name)

            if isinstance(error, ImageRenderError):
                form.add_error(None, str(error))
            else:
                logger.exception("Post generation failed")
                form.add_error(
                    None,
                    "We couldn't generate this post. Please try again.",
                )

        else:
            if caption_data["used_ai"]:
                messages.success(request, "Your post is ready.")
            else:
                messages.info(
                    request,
                    "Your image is ready with a basic caption. "
                    "AI captions are unavailable right now.",
                )

            return redirect("posts:detail", pk=post.pk)

        finally:
            if image_file is not None:
                image_file.close()

    return render(
        request,
        "posts/post_form.html",
        {"form": form},
    )


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