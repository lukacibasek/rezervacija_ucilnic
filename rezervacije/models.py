from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Ucilnica(models.Model):
    oznaka = models.CharField("oznaka", max_length=20, unique=True)
    kapaciteta = models.PositiveIntegerField("kapaciteta")
    opis = models.TextField("opis", blank=True)

    class Meta:
        ordering = ["oznaka"]
        verbose_name = "učilnica"
        verbose_name_plural = "učilnice"

    def __str__(self):
        return self.oznaka

    def get_absolute_url(self):
        return reverse("rezervacije:ucilnica_detail", args=[self.pk])


class Rezervacija(models.Model):
    ucilnica = models.ForeignKey(
        Ucilnica,
        on_delete=models.CASCADE,
        related_name="rezervacije",
        verbose_name="učilnica",
    )
    uporabnik = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rezervacije",
        verbose_name="uporabnik",
    )
    datum = models.DateField("datum")
    ura_od = models.TimeField("ura od")
    ura_do = models.TimeField("ura do")
    namen = models.CharField("namen", max_length=200)
    ustvarjeno = models.DateTimeField("ustvarjeno", auto_now_add=True)

    class Meta:
        ordering = ["datum", "ura_od"]
        verbose_name = "rezervacija"
        verbose_name_plural = "rezervacije"

    def __str__(self):
        return f"{self.ucilnica} {self.datum} {self.ura_od:%H:%M}–{self.ura_do:%H:%M}"

    def clean(self):
        errors = {}

        if self.ura_od and self.ura_do and self.ura_od >= self.ura_do:
            errors["ura_do"] = "Ura konca mora biti kasnejša od ure začetka."

        if self.datum and self.datum < timezone.localdate():
            errors["datum"] = "Rezervacije ni mogoče ustvariti za pretekli datum."

        if errors:
            raise ValidationError(errors)

        if self.ucilnica_id and self.datum and self.ura_od and self.ura_do:
            prekrivanja = Rezervacija.objects.filter(
                ucilnica_id=self.ucilnica_id,
                datum=self.datum,
                ura_od__lt=self.ura_do,
                ura_do__gt=self.ura_od,
            )
            if self.pk:
                prekrivanja = prekrivanja.exclude(pk=self.pk)
            obstojeca = prekrivanja.first()
            if obstojeca:
                raise ValidationError(
                    f"Učilnica {obstojeca.ucilnica} je ta dan že rezervirana "
                    f"od {obstojeca.ura_od:%H:%M} do {obstojeca.ura_do:%H:%M}. "
                    "Izberite drug termin ali drugo učilnico."
                )
