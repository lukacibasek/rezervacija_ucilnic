from django.contrib import admin

from .models import Rezervacija, Ucilnica


@admin.register(Ucilnica)
class UcilnicaAdmin(admin.ModelAdmin):
    list_display = ("oznaka", "kapaciteta")
    search_fields = ("oznaka",)


@admin.register(Rezervacija)
class RezervacijaAdmin(admin.ModelAdmin):
    list_display = ("ucilnica", "uporabnik", "datum", "ura_od", "ura_do")
    list_filter = ("ucilnica", "datum")
