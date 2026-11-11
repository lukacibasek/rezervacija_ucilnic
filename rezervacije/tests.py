from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Rezervacija, Ucilnica

User = get_user_model()


class RezervacijaTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.jutri = timezone.localdate() + timedelta(days=1)
        cls.ucilnica = Ucilnica.objects.create(oznaka="R12", kapaciteta=30)
        cls.ana = User.objects.create_user("ana", password="geslo12345")
        cls.bor = User.objects.create_user("bor", password="geslo12345")
        cls.rezervacija = Rezervacija.objects.create(
            ucilnica=cls.ucilnica,
            uporabnik=cls.ana,
            datum=cls.jutri,
            ura_od=time(8, 0),
            ura_do=time(10, 0),
            namen="Matematika",
        )


class PrekrivanjeTest(RezervacijaTestBase):
    def test_prekrivajoca_rezervacija_je_zavrnjena(self):
        nova = Rezervacija(
            ucilnica=self.ucilnica,
            uporabnik=self.bor,
            datum=self.jutri,
            ura_od=time(9, 0),
            ura_do=time(11, 0),
            namen="Fizika",
        )
        with self.assertRaises(ValidationError):
            nova.full_clean()

    def test_prekrivanje_zavrne_tudi_obrazec(self):
        self.client.force_login(self.bor)
        response = self.client.post(
            reverse("rezervacije:nova"),
            {
                "ucilnica": self.ucilnica.pk,
                "datum": self.jutri.isoformat(),
                "ura_od": "09:30",
                "ura_do": "10:30",
                "namen": "Fizika",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "že rezervirana")
        self.assertEqual(Rezervacija.objects.count(), 1)

    def test_zaporedna_rezervacija_je_dovoljena(self):
        nova = Rezervacija(
            ucilnica=self.ucilnica,
            uporabnik=self.bor,
            datum=self.jutri,
            ura_od=time(10, 0),
            ura_do=time(11, 0),
            namen="Fizika",
        )
        nova.full_clean()


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


class SeznamUcilnicTest(TestCase):
    def test_prazen_seznam_prikaze_sporocilo(self):
        response = self.client.get(reverse("rezervacije:ucilnica_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trenutno ni na voljo nobene učilnice.")
