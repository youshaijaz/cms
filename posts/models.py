from django.core.validators import RegexValidator
from django.db import models

from brands.models import Brand


color_validator = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message="Enter a color like #2563EB.",
)


class PostTemplate(models.Model):
    name = models.CharField(max_length=100)
    layout = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    template = models.ForeignKey(
        PostTemplate,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    headline = models.CharField(max_length=100)
    body_text = models.CharField(max_length=300, blank=True)

    background_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[color_validator],
    )
    text_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[color_validator],
    )

    caption = models.TextField(blank=True)
    hashtags = models.TextField(blank=True)
    image = models.ImageField(upload_to="posts/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.brand.name}: {self.headline}"

    @property
    def full_caption(self):
        return "\n\n".join(
            part for part in [self.caption, self.hashtags] if part
        )


class PostPhoto(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    position = models.PositiveSmallIntegerField()
    image = models.ImageField(upload_to="post_photos/")

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "position"],
                name="unique_post_photo_position",
            )
        ]