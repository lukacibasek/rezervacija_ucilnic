from django import forms

from .models import Rezervacija


class RezervacijaForm(forms.ModelForm):
    class Meta:
        model = Rezervacija
        fields = ["ucilnica", "datum", "ura_od", "ura_do", "namen"]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "ura_od": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "ura_do": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }
