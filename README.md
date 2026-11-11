# Rezervacije učilnic

Spletna aplikacija v Djangu za rezervacijo šolskih učilnic. Vsak si lahko ogleda
seznam učilnic in njihove prihajajoče rezervacije, prijavljeni uporabniki pa lahko
učilnice rezervirajo ter svoje rezervacije urejajo in prekličejo. Administrator
učilnice in rezervacije upravlja v Django adminu.

## Člani ekipe

| Član | Prispevek |
|------|-----------|
| Valentin Križaj | _(dopolni: kaj je naredil)_ |
| Žiga Mav | _(dopolni: kaj je naredil)_ |
| Luka Čibašek | _(dopolni: kaj je naredil)_ |

## Namestitev in zagon

Potrebuješ Python 3.12 ali novejši (razvijano s Pythonom 3.14).

```bash
# 1. Ustvari in aktiviraj virtualno okolje
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 2. Namesti odvisnosti
pip install -r requirements.txt

# 3. Pripravi podatkovno bazo
python manage.py migrate

# 4. Naloži začetne učilnice (SŠTS Šiška)
python manage.py loaddata ucilnice

# 5. Ustvari administratorja (za Django admin)
python manage.py createsuperuser

# 6. Zaženi razvojni strežnik
python manage.py runserver
```

Aplikacija je nato dostopna na <http://127.0.0.1:8000/>, admin pa na
<http://127.0.0.1:8000/admin/>. Korak 4 naloži 14 učilnic Srednje šole tehniških
strok Šiška; ukaz lahko varno ponoviš, saj učilnice prepozna po oznaki in jih ne
podvoji. Dodatne učilnice in uporabniške račune dodaš v adminu.

Testi se zaženejo z ukazom:

```bash
python manage.py test
```

## Glavne funkcionalnosti

- Javni seznam učilnic (oznaka, kapaciteta, opis) s prijaznim sporočilom, če učilnic še ni.
- Javna stran posamezne učilnice s prihajajočimi rezervacijami.
- Prijava in odjava uporabnikov.
- Ustvarjanje nove rezervacije (učilnica, datum, ura od–do, namen).
- Pregled lastnih rezervacij ter njihovo urejanje in preklic (s potrditveno stranjo).
- Preverjanje pravilnosti: ura začetka mora biti pred uro konca, datum ne sme biti
  v preteklosti, rezervacija se ne sme prekrivati z drugo rezervacijo iste učilnice.
- Uporabnik lahko ureja in prekliče samo svoje rezervacije (do tujih dobi napako 404).
- Upravljanje učilnic in rezervacij v Django adminu (iskanje, filtri).

## Znane omejitve

- Registracije novih uporabnikov ni; račune ustvari administrator v adminu.
- Ni ponavljajočih se rezervacij (npr. vsak teden ob isti uri).
- Ni preverjanja delovnega časa šole ali kapacitete glede na število udeležencev.
- Preverjanje prekrivanja poteka na ravni aplikacije, zato bi lahko dve hkratni
  zahtevi v redkih primerih ustvarili prekrivajoči se rezervaciji.
- Pretekle rezervacije ni mogoče urejati (datum ne sme biti v preteklosti).
- Nastavitve (`SECRET_KEY`, `DEBUG = True`) so namenjene samo razvoju, ne produkciji.

## Delo po sprintih, Kanban in Git

_(dopolni: kako smo delo razdelili na sprinte, kako smo uporabljali Kanban tablo
— stolpci, naloge, kdo je kaj prevzel — in kako smo delali z Gitom — veje,
commiti, pull requesti, pregledi kode.)_

## Rezultati preverjanja

Preverjeno 11. 11. 2026 z Djangom 6.1.2 in Pythonom 3.14:

- `python manage.py makemigrations` – brez novih sprememb (migracija `0001_initial` je v repozitoriju).
- `python manage.py migrate` – uspešno.
- `python manage.py check` – „System check identified no issues (0 silenced).“
- `python manage.py test` – 6 testov, vsi uspešni (OK):
  - prekrivajoča rezervacija iste učilnice je zavrnjena (model in obrazec),
  - zaporedna rezervacija (konec ene = začetek druge) je dovoljena,
  - anonimni uporabnik je pri `/rezervacije/nova/` preusmerjen na prijavo,
  - uporabnik ne more preklicati tuje rezervacije (404),
  - prazen seznam učilnic prikaže sporočilo.
- Ročni pregled vseh strani s testnim odjemalcem (seznam, podrobnosti, prijava,
  nova rezervacija, moje rezervacije, urejanje, preklic, odjava) – vse delujejo.
