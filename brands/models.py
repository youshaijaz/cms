from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


hex_color_validator = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message="Enter a color like #2563EB.",
)


class Brand(models.Model):
    class Tone(models.TextChoices):
        PROFESSIONAL = "professional", "Professional"
        FRIENDLY = "friendly", "Friendly"
        PLAYFUL = "playful", "Playful"
        LUXURY = "luxury", "Luxury"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="brands",
    )
    name = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    primary_color = models.CharField(
        max_length=7,
        default="#2563EB",
        validators=[hex_color_validator],
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#FFFFFF",
        validators=[hex_color_validator],
    )
    logo = models.ImageField(upload_to="logos/", blank=True)
    tone = models.CharField(
        max_length=20,
        choices=Tone.choices,
        default=Tone.FRIENDLY,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name