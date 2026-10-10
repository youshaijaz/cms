from django.urls import path

from . import views


app_name = "posts"

urlpatterns = [
    path("new/", views.post_create, name="create"),
    path("<int:pk>/", views.post_detail, name="detail"),
    path("<int:pk>/image/", views.post_image, name="image"),
    path(
        "<int:pk>/caption/download/",
        views.post_caption_download,
        name="caption_download",
    ),
]