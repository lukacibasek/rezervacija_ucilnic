from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


# Šolske ure: številka ure -> (začetek, konec). Edini vir resnice za čase ur.
SOLSKE_URE = {
    0: (time(7, 10), time(7, 55)),
    1: (time(8, 0), time(8, 45)),
    2: (time(8, 50), time(9, 35)),
    3: (time(9, 40), time(10, 25)),
    4: (time(10, 30), time(11, 15)),
    5: (time(11, 20), time(12, 5)),
    6: (time(12, 10), time(12, 55)),
    7: (time(13, 0), time(13, 45)),
    8: (time(13, 50), time(14, 35)),
    9: (time(14, 40), time(15, 25)),
    10: (time(15, 30), time(16, 15)),
}


def naziv_ure(st):
    return "Predura" if st == 0 else f"{st}. ura"


def _oznaka_ure(st, od, do):
    return f"{naziv_ure(st)} ({od.hour}.{od:%M}-{do.hour}.{do:%M})"


SOLSKA_URA_CHOICES = [(st, _oznaka_ure(st, od, do)) for st, (od, do) in SOLSKE_URE.items()]

NAPAKA_ZASEDENO = "Ta učilnica je v tem terminu že rezervirana."


class UcilnicaManager(models.Manager):
    def get_by_natural_key(self, oznaka):
        return self.get(oznaka=oznaka)


class Ucilnica(models.Model):
    oznaka = models.CharField("oznaka", max_length=20, unique=True)
    kapaciteta = models.PositiveIntegerField("kapaciteta")
    opis = models.TextField("opis", blank=True)

    objects = UcilnicaManager()

    class Meta:
        ordering = ["oznaka"]
        verbose_name = "učilnica"
        verbose_name_plural = "učilnice"

    def __str__(self):
        return self.oznaka

    def natural_key(self):
        return (self.oznaka,)

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
    solska_ura = models.PositiveSmallIntegerField("šolska ura", choices=SOLSKA_URA_CHOICES)
    namen = models.CharField("namen", max_length=200)
    ustvarjeno = models.DateTimeField("ustvarjeno", auto_now_add=True)

    class Meta:
        ordering = ["datum", "solska_ura"]
        verbose_name = "rezervacija"
        verbose_name_plural = "rezervacije"
        constraints = [
            models.UniqueConstraint(
                fields=["ucilnica", "datum", "solska_ura"],
                name="unikatna_rezervacija_termina",
                violation_error_message=NAPAKA_ZASEDENO,
            ),
        ]

    def __str__(self):
        return f"{self.ucilnica} {self.datum} {self.get_solska_ura_display()}"

    @property
    def naziv_ure(self):
        return naziv_ure(self.solska_ura)

    @property
    def ura_od(self):
        return SOLSKE_URE[self.solska_ura][0]

    @property
    def ura_do(self):
        return SOLSKE_URE[self.solska_ura][1]

    def clean(self):
        if self.datum:
            if self.datum < timezone.localdate():
                raise ValidationError(
                    {"datum": "Rezervacije ni mogoče ustvariti za pretekli datum."}
                )
            if self.datum.weekday() >= 5:
                raise ValidationError(
                    {"datum": "Ob sobotah in nedeljah rezervacije niso mogoče."}
                )

    def unique_error_message(self, model_class, unique_check):
        # Neparcialni UniqueConstraint uporablja to sporočilo namesto violation_error_message.
        if set(unique_check) == {"ucilnica", "datum", "solska_ura"}:
            return ValidationError(NAPAKA_ZASEDENO, code="unique_together")
        return super().unique_error_message(model_class, unique_check)
