from django import forms

from brands.models import Brand
from .models import Post, PostTemplate
from .services.template_catalog import TEMPLATES


class PostForm(forms.ModelForm):
    photo_1 = forms.ImageField(required=False)
    photo_2 = forms.ImageField(required=False)
    photo_3 = forms.ImageField(required=False)
    photo_4 = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = [
            "brand",
            "template",
            "headline",
            "body_text",
            "background_color",
            "text_color",
        ]
        widgets = {
            "headline": forms.TextInput(
                attrs={"placeholder": "Your next great headline"}
            ),
            "body_text": forms.Textarea(attrs={"rows": 3}),
            "template": forms.RadioSelect(),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["brand"].queryset = Brand.objects.filter(owner=user)
        self.fields["template"].queryset = PostTemplate.objects.filter(
            is_active=True,
            layout__in=TEMPLATES,
        ).order_by("name")

        for name in ["background_color", "text_color"]:
            self.fields[name].widget = forms.TextInput(
                attrs={"placeholder": "#D4F66A"}
            )
            self.fields[name].help_text = (
                "Optional hex color. Leave blank to use the design’s defaults."
            )

        self.existing_photos = {}

        if self.instance.pk:
            self.existing_photos = {
                photo.position: photo
                for photo in self.instance.photos.all()
            }

    @property
    def photo_fields(self):
        return [self[f"photo_{index}"] for index in range(1, 5)]

    def clean_headline(self):
        value = self.cleaned_data["headline"].strip()

        if not value:
            raise forms.ValidationError("Enter a headline.")

        return value

    def clean(self):
        cleaned = super().clean()
        template = cleaned.get("template")

        if not template or template.layout not in TEMPLATES:
            return cleaned

        required_count = len(TEMPLATES[template.layout]["slots"])

        for index in range(1, 5):
            name = f"photo_{index}"
            uploaded = cleaned.get(name)

            if uploaded:
                if uploaded.size > 8 * 1024 * 1024:
                    self.add_error(name, "Use a photo smaller than 8 MB.")

                image = uploaded.image

                if image.width * image.height > 25_000_000:
                    self.add_error(
                        name,
                        "Use an image with fewer than 25 million pixels.",
                    )

            if (
                index <= required_count
                and not uploaded
                and index not in self.existing_photos
                and name not in self.errors
            ):
                self.add_error(
                    name,
                    f"This design needs {required_count} photos. "
                    f"Please upload photo {index}.",
                )

            if uploaded and index > required_count:
                self.add_error(
                    name,
                    f"This design only uses {required_count} photos.",
                )

        return cleaned