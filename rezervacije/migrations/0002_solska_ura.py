from datetime import time

from django.db import migrations, models

# Začetki ur ob času te migracije (namenoma kopirano, migracije ne smejo uvažati modelov).
ZACETKI_UR = [
    (0, time(7, 10)),
    (1, time(8, 0)),
    (2, time(8, 50)),
    (3, time(9, 40)),
    (4, time(10, 30)),
    (5, time(11, 20)),
    (6, time(12, 10)),
    (7, time(13, 0)),
    (8, time(13, 50)),
    (9, time(14, 40)),
    (10, time(15, 30)),
]


def ura_iz_casa(cas):
    """Zadnja šolska ura, ki se začne najkasneje ob danem času (sicer predura)."""
    izbrana = 0
    for st, zacetek in ZACETKI_UR:
        if zacetek <= cas:
            izbrana = st
    return izbrana


def pretvori_obstojece(apps, schema_editor):
    Rezervacija = apps.get_model("rezervacije", "Rezervacija")
    for rezervacija in Rezervacija.objects.all():
        rezervacija.solska_ura = ura_iz_casa(rezervacija.ura_od)
        rezervacija.save(update_fields=["solska_ura"])


class Migration(migrations.Migration):

    dependencies = [
        ("rezervacije", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="rezervacija",
            name="solska_ura",
            field=models.PositiveSmallIntegerField(null=True, verbose_name="šolska ura"),
        ),
        migrations.RunPython(pretvori_obstojece, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="rezervacija",
            options={
                "ordering": ["datum", "solska_ura"],
                "verbose_name": "rezervacija",
                "verbose_name_plural": "rezervacije",
            },
        ),
        migrations.RemoveField(model_name="rezervacija", name="ura_od"),
        migrations.RemoveField(model_name="rezervacija", name="ura_do"),
        migrations.AlterField(
            model_name="rezervacija",
            name="solska_ura",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Predura (7.10-7.55)"),
                    (1, "1. ura (8.00-8.45)"),
                    (2, "2. ura (8.50-9.35)"),
                    (3, "3. ura (9.40-10.25)"),
                    (4, "4. ura (10.30-11.15)"),
                    (5, "5. ura (11.20-12.05)"),
                    (6, "6. ura (12.10-12.55)"),
                    (7, "7. ura (13.00-13.45)"),
                    (8, "8. ura (13.50-14.35)"),
                    (9, "9. ura (14.40-15.25)"),
                    (10, "10. ura (15.30-16.15)"),
                ],
                verbose_name="šolska ura",
            ),
        ),
        migrations.AddConstraint(
            model_name="rezervacija",
            constraint=models.UniqueConstraint(
                fields=("ucilnica", "datum", "solska_ura"),
                name="unikatna_rezervacija_termina",
                violation_error_message="Ta učilnica je v tem terminu že rezervirana.",
            ),
        ),
    ]
