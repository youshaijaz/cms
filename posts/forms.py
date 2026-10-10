from django import forms

from brands.models import Brand
from .models import Post, PostTemplate


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["brand", "template", "headline", "body_text"]
        widgets = {
            "headline": forms.TextInput(
                attrs={"placeholder": "Something worth sharing"}
            ),
            "body_text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Add a short message for your image",
                }
            ),
            "template": forms.RadioSelect(),
        }
        labels = {
            "body_text": "Text on the image",
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["brand"].queryset = Brand.objects.filter(owner=user)
        self.fields["template"].queryset = PostTemplate.objects.filter(
            is_active=True
        )
        self.fields["brand"].empty_label = "Choose a brand"

    def clean_headline(self):
        headline = self.cleaned_data["headline"].strip()

        if not headline:
            raise forms.ValidationError("Enter a headline.")

        return headline