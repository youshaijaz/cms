from django.db import models

from brands.models import Brand


class PostTemplate(models.Model):
    class Layout(models.TextChoices):
        BOLD = "bold", "Bold announcement"
        MINIMAL = "minimal", "Minimal editorial"

    name = models.CharField(max_length=100)
    layout = models.CharField(
        max_length=20,
        choices=Layout.choices,
        unique=True,
    )
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
