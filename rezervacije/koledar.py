"""Tedenski koledar zasedenosti učilnice (skupna logika za stran učilnice in /koledar/)."""

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urlencode

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse
from django.utils import timezone

from .models import SOLSKE_URE, Rezervacija, naziv_ure

IMENA_DNI = ["Pon", "Tor", "Sre", "Čet", "Pet"]

PROSTO = "prosto"
ZASEDENO = "zasedeno"
MOJA = "moja"
PRETEKLO = "preteklo"


@dataclass
class Celica:
    stanje: str
    datum: date
    solska_ura: int
    rezervacija: Rezervacija | None = None
    url: str = ""


def privzeti_ponedeljek(danes):
    """Ponedeljek tekočega tedna; ob sobotah in nedeljah ponedeljek naslednjega tedna."""
    ponedeljek = danes - timedelta(days=danes.weekday())
    if danes.weekday() >= 5:
        ponedeljek += timedelta(days=7)
    return ponedeljek


def izberi_ponedeljek(vrednost, danes):
    """Ponedeljek tedna iz ?teden=YYYY-MM-DD; neveljavna vrednost vrne privzeti teden."""
    try:
        izbran = date.fromisoformat(vrednost)
    except (TypeError, ValueError):
        return privzeti_ponedeljek(danes)
    return izbran - timedelta(days=izbran.weekday())


def _je_preteklo(datum, ura, zdaj):
    if datum != zdaj.date():
        return datum < zdaj.date()
    return SOLSKE_URE[ura][1] <= zdaj.time()


def _url_nova(ucilnica, datum, ura, uporabnik):
    url = reverse("rezervacije:nova") + "?" + urlencode(
        {"ucilnica": ucilnica.pk, "datum": datum.isoformat(), "solska_ura": ura}
    )
    if uporabnik.is_authenticated:
        return url
    return reverse("login") + "?" + urlencode({REDIRECT_FIELD_NAME: url})


def tedenski_koledar(ucilnica, teden_param, uporabnik, dodatni_parametri=None):
    """Pripravi vse, kar predloga potrebuje za tedensko mrežo izbrane učilnice."""
    zdaj = timezone.localtime()
    danes = zdaj.date()
    najmanjsi = privzeti_ponedeljek(danes)
    ponedeljek = izberi_ponedeljek(teden_param, danes)
    dnevi = [ponedeljek + timedelta(days=i) for i in range(5)]

    rezervacije = {
        (r.datum, r.solska_ura): r
        for r in Rezervacija.objects.filter(
            ucilnica=ucilnica, datum__range=(dnevi[0], dnevi[-1])
        ).select_related("uporabnik")
    }

    vrstice = []
    for ura, (od, do) in SOLSKE_URE.items():
        celice = []
        for dan in dnevi:
            rez = rezervacije.get((dan, ura))
            if _je_preteklo(dan, ura, zdaj):
                celica = Celica(PRETEKLO, dan, ura, rez)
            elif rez is None:
                celica = Celica(PROSTO, dan, ura, url=_url_nova(ucilnica, dan, ura, uporabnik))
            elif rez.uporabnik_id == uporabnik.pk:
                celica = Celica(MOJA, dan, ura, rez, url=reverse("rezervacije:uredi", args=[rez.pk]))
            else:
                celica = Celica(ZASEDENO, dan, ura, rez)
            celice.append(celica)
        vrstice.append({"ura": ura, "naziv": naziv_ure(ura), "od": od, "do": do, "celice": celice})

    def povezava(pon):
        parametri = dict(dodatni_parametri or {}, teden=pon.isoformat())
        return "?" + urlencode(parametri)

    return {
        "dnevi": [
            {"datum": d, "oznaka": f"{IMENA_DNI[i]}, {d.day}. {d.month}.", "danes": d == danes}
            for i, d in enumerate(dnevi)
        ],
        "vrstice": vrstice,
        "danes": danes,
        "od": dnevi[0],
        "do": dnevi[-1],
        "prejsnji": povezava(ponedeljek - timedelta(days=7)) if ponedeljek > najmanjsi else "",
        "ta": povezava(najmanjsi),
        "naslednji": povezava(ponedeljek + timedelta(days=7)),
        "je_ta_teden": ponedeljek == najmanjsi,
    }
