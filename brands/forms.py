from django import forms

from .models import Brand


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = [
            "name",
            "industry",
            "primary_color",
            "secondary_color",
            "logo",
            "tone",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Example: Yousha's Coffee"}
            ),
            "industry": forms.TextInput(
                attrs={"placeholder": "Example: Coffee shop"}
            ),
            "primary_color": forms.TextInput(attrs={"type": "color"}),
            "secondary_color": forms.TextInput(attrs={"type": "color"}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")

        if logo and logo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Logo must be 5 MB or smaller.")

        return logo
    