from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .koledar import MOJA, PROSTO, ZASEDENO, privzeti_ponedeljek
from .models import Rezervacija, Ucilnica

User = get_user_model()

NAPAKA_ZASEDENO = "Ta učilnica je v tem terminu že rezervirana."


def naslednji_delovnik():
    """Prvi delovni dan (pon–pet) po današnjem."""
    dan = timezone.localdate() + timedelta(days=1)
    while dan.weekday() >= 5:
        dan += timedelta(days=1)
    return dan


def naslednja_sobota():
    dan = timezone.localdate() + timedelta(days=1)
    while dan.weekday() != 5:
        dan += timedelta(days=1)
    return dan


class RezervacijaTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.delovnik = naslednji_delovnik()
        cls.ucilnica = Ucilnica.objects.create(oznaka="1100", kapaciteta=30)
        cls.ana = User.objects.create_user("ana", password="geslo12345")
        cls.bor = User.objects.create_user("bor", password="geslo12345")
        cls.rezervacija = Rezervacija.objects.create(
            ucilnica=cls.ucilnica,
            uporabnik=cls.ana,
            datum=cls.delovnik,
            solska_ura=3,
            namen="Matematika",
        )

    def nova(self, **kwargs):
        podatki = {
            "ucilnica": self.ucilnica,
            "uporabnik": self.bor,
            "datum": self.delovnik,
            "solska_ura": 3,
            "namen": "Fizika",
        }
        podatki.update(kwargs)
        return Rezervacija(**podatki)


class TerminTest(RezervacijaTestBase):
    def test_ista_ucilnica_in_ura_je_zavrnjena(self):
        with self.assertRaisesMessage(ValidationError, NAPAKA_ZASEDENO):
            self.nova().full_clean()

    def test_zasedenost_zavrne_tudi_obrazec(self):
        self.client.force_login(self.bor)
        response = self.client.post(
            reverse("rezervacije:nova"),
            {
                "ucilnica": self.ucilnica.pk,
                "datum": self.delovnik.isoformat(),
                "solska_ura": 3,
                "namen": "Fizika",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NAPAKA_ZASEDENO)
        self.assertEqual(Rezervacija.objects.count(), 1)

    def test_druga_ura_je_dovoljena(self):
        self.nova(solska_ura=4).full_clean()

    def test_urejanje_lastne_rezervacije_ni_konflikt(self):
        self.rezervacija.namen = "Matematika – popravljeno"
        self.rezervacija.full_clean()

    def test_sobota_je_zavrnjena(self):
        with self.assertRaisesMessage(ValidationError, "Ob sobotah in nedeljah"):
            self.nova(datum=naslednja_sobota()).full_clean()

    def test_pretekli_datum_je_zavrnjen(self):
        with self.assertRaisesMessage(ValidationError, "pretekli datum"):
            self.nova(datum=timezone.localdate() - timedelta(days=7)).full_clean()

    def test_casi_ure_izhajajo_iz_konstante(self):
        r = self.nova(solska_ura=0)
        self.assertEqual((r.ura_od, r.ura_do), (time(7, 10), time(7, 55)))
        r.solska_ura = 10
        self.assertEqual((r.ura_od, r.ura_do), (time(15, 30), time(16, 15)))
        self.assertEqual(self.nova(solska_ura=1).get_solska_ura_display(), "1. ura (8.00-8.45)")


class DostopTest(RezervacijaTestBase):
    def test_anonimni_uporabnik_je_preusmerjen_na_prijavo(self):
        url = reverse("rezervacije:nova")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_uporabnik_ne_more_preklicati_tuje_rezervacije(self):
        self.client.force_login(self.bor)
        url = reverse("rezervacije:preklici", args=[self.rezervacija.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Rezervacija.objects.filter(pk=self.rezervacija.pk).exists())


class PodrobnostiUcilniceTest(RezervacijaTestBase):
    def test_prikaze_uro_in_cas(self):
        response = self.client.get(
            self.ucilnica.get_absolute_url(), {"teden": self.delovnik.isoformat()}
        )
        self.assertContains(response, "3. ura")
        self.assertContains(response, "9.40–10.25")
        self.assertContains(response, "Matematika")


class SeznamUcilnicTest(TestCase):
    def test_prazen_seznam_prikaze_sporocilo(self):
        response = self.client.get(reverse("rezervacije:ucilnica_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trenutno ni na voljo nobene učilnice.")

    def test_fixture_nalozi_ucilnice_po_oznaki(self):
        call_command("loaddata", "ucilnice", verbosity=0)
        call_command("loaddata", "ucilnice", verbosity=0)  # ponovni zagon ne podvaja
        response = self.client.get(reverse("rezervacije:ucilnica_list"))
        oznake = [u.oznaka for u in response.context["ucilnice"]]
        self.assertEqual(len(oznake), 14)
        self.assertEqual(oznake, sorted(oznake))
        self.assertEqual(oznake[0], "0240")
        self.assertEqual(oznake[-1], "T1070")


class KoledarTest(RezervacijaTestBase):
    def celica(self, response, ura):
        """Celica izbrane šolske ure na dan testne rezervacije."""
        koledar = response.context["koledar"]
        dan = [d["datum"] for d in koledar["dnevi"]].index(self.delovnik)
        return koledar["vrstice"][ura]["celice"][dan]

    def odpri(self, url=None):
        return self.client.get(
            url or self.ucilnica.get_absolute_url(), {"teden": self.delovnik.isoformat()}
        )

    def test_zasedena_in_prosta_ura(self):
        self.client.force_login(self.bor)
        response = self.odpri()
        zasedena = self.celica(response, 3)
        self.assertEqual(zasedena.stanje, ZASEDENO)
        self.assertEqual(zasedena.url, "")
        self.assertContains(response, "slot--zasedeno")
        self.assertContains(response, "Matematika")

        prosta = self.celica(response, 4)
        self.assertEqual(prosta.stanje, PROSTO)
        pricakovan = (
            f"{reverse('rezervacije:nova')}?ucilnica={self.ucilnica.pk}"
            f"&datum={self.delovnik.isoformat()}&solska_ura=4"
        )
        self.assertEqual(prosta.url, pricakovan)
        self.assertContains(response, pricakovan.replace("&", "&amp;"))

    def test_prosta_ura_za_anonimnega_vodi_na_prijavo(self):
        prosta = self.celica(self.odpri(), 4)
        self.assertTrue(prosta.url.startswith(reverse("login") + "?next="))
        self.assertIn("solska_ura%3D4", prosta.url)

    def test_lastna_rezervacija_je_oznacena(self):
        self.client.force_login(self.ana)
        response = self.odpri()
        moja = self.celica(response, 3)
        self.assertEqual(moja.stanje, MOJA)
        self.assertEqual(moja.url, reverse("rezervacije:uredi", args=[self.rezervacija.pk]))
        self.assertContains(response, "Moja")

    def test_neveljaven_teden_prikaze_privzeti_teden(self):
        response = self.client.get(self.ucilnica.get_absolute_url(), {"teden": "ni-datum"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["koledar"]["od"], privzeti_ponedeljek(timezone.localdate())
        )

    def test_stran_koledar_privzeto_prva_ucilnica(self):
        Ucilnica.objects.create(oznaka="0240", kapaciteta=16)
        response = self.client.get(reverse("rezervacije:koledar"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["ucilnica"].oznaka, "0240")


class PredizpolnjenObrazecTest(RezervacijaTestBase):
    def test_obrazec_prevzame_parametre(self):
        self.client.force_login(self.bor)
        response = self.client.get(
            reverse("rezervacije:nova"),
            {"ucilnica": self.ucilnica.pk, "datum": self.delovnik.isoformat(), "solska_ura": 5},
        )
        initial = response.context["form"].initial
        self.assertEqual(initial["ucilnica"], self.ucilnica)
        self.assertEqual(initial["datum"], self.delovnik)
        self.assertEqual(initial["solska_ura"], 5)

    def test_neveljavni_parametri_so_prezrti(self):
        self.client.force_login(self.bor)
        response = self.client.get(
            reverse("rezervacije:nova"), {"ucilnica": "x", "datum": "31.2.", "solska_ura": 99}
        )
        self.assertEqual(response.context["form"].initial, {})
