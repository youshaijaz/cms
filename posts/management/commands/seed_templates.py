from django.core.management.base import BaseCommand

from posts.models import PostTemplate


class Command(BaseCommand):
    help = "Create the starter post templates."

    def handle(self, *args, **options):
        templates = [
            {
                "layout": "bold",
                "name": "Bold announcement",
                "description": (
                    "Your primary color, a large headline, "
                    "and a short supporting message."
                ),
            },
            {
                "layout": "minimal",
                "name": "Minimal editorial",
                "description": (
                    "Your secondary color, clean typography, "
                    "and a primary-color accent."
                ),
            },
        ]

        for template in templates:
            layout = template.pop("layout")

            PostTemplate.objects.update_or_create(
                layout=layout,
                defaults={**template, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS("Starter templates are ready."))