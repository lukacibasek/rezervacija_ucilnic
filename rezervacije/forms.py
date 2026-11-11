from django import forms

from .models import Rezervacija


class RezervacijaForm(forms.ModelForm):
    class Meta:
        model = Rezervacija
        fields = ["ucilnica", "datum", "solska_ura", "namen"]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
