from django.core.management.base import BaseCommand

from posts.models import PostTemplate
from posts.services.template_catalog import TEMPLATES


class Command(BaseCommand):
    help = "Create the 20 photo templates."

    def handle(self, *args, **options):
        PostTemplate.objects.exclude(
            layout__in=TEMPLATES
        ).update(is_active=False)

        for layout, spec in TEMPLATES.items():
            PostTemplate.objects.update_or_create(
                layout=layout,
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(TEMPLATES)} photo templates are ready."
            )
        )