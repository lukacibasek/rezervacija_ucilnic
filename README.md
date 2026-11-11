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
- Začetni seznam 14 učilnic SŠTS Šiška (`python manage.py loaddata ucilnice`), urejen po oznaki.
- Ustvarjanje nove rezervacije za šolsko uro (učilnica, datum, šolska ura 0–10, namen).
  Čas posamezne ure (npr. 1. ura 8.00–8.45) je določen v programu in se izpiše samodejno.
- Pregled lastnih rezervacij ter njihovo urejanje in preklic (s potrditveno stranjo).
- Koledar zasedenosti: tedenska mreža (pon–pet × šolske ure) na strani učilnice in na
  strani `/koledar/` z izbiro učilnice. Prosti termini so povezava na predizpolnjen
  obrazec, lastne rezervacije vodijo na urejanje, pretekli termini so posivljeni;
  med tedni se premikaš z gumbi ali parametrom `?teden=LLLL-MM-DD`.
- Preverjanje pravilnosti: datum ne sme biti v preteklosti ne na soboto ali nedeljo,
  učilnica je lahko v isti šolski uri istega dne rezervirana le enkrat
  (zagotovljeno tudi z omejitvijo v podatkovni bazi).
- Uporabnik lahko ureja in prekliče samo svoje rezervacije (do tujih dobi napako 404).
- Upravljanje učilnic in rezervacij v Django adminu (iskanje, filtri).

## Znane omejitve

- Registracije novih uporabnikov ni; račune ustvari administrator v adminu.
- Ni ponavljajočih se rezervacij (npr. vsak teden ob isti uri).
- Rezervira se lahko samo ena šolska ura naenkrat; za blok ur je treba narediti
  več rezervacij.
- Praznikov in počitnic aplikacija ne pozna (zavrne samo sobote in nedelje).
- Ni preverjanja kapacitete glede na število udeležencev.
- Časi šolskih ur so zapisani v kodi (`SOLSKE_URE` v `rezervacije/models.py`),
  ne v adminu.
- Pretekle rezervacije ni mogoče urejati (datum ne sme biti v preteklosti).
- Nastavitve (`SECRET_KEY`, `DEBUG = True`) so namenjene samo razvoju, ne produkciji.

## Delo po sprintih, Kanban in Git

_(dopolni: kako smo delo razdelili na sprinte, kako smo uporabljali Kanban tablo
— stolpci, naloge, kdo je kaj prevzel — in kako smo delali z Gitom — veje,
commiti, pull requesti, pregledi kode.)_

## Rezultati preverjanja

Preverjeno 11. 11. 2026 z Djangom 6.1.2 in Pythonom 3.14:

- `python manage.py makemigrations` – brez novih sprememb (migraciji `0001_initial`
  in `0002_solska_ura` sta v repozitoriju; `0002` obstoječe rezervacije pretvori
  v šolsko uro glede na uro začetka).
- `python manage.py migrate` – uspešno.
- `python manage.py loaddata ucilnice` – „Installed 14 object(s) from 1 fixture(s)“;
  ponovni zagon učilnic ne podvoji.
- `python manage.py check` – „System check identified no issues (0 silenced).“
- `python manage.py test` – 19 testov, vsi uspešni (OK):
  - rezervacija iste učilnice v isti šolski uri je zavrnjena (model in obrazec),
  - druga šolska ura iste učilnice je dovoljena, urejanje lastne rezervacije ni konflikt,
  - sobota in pretekli datum sta zavrnjena,
  - časi ur (`ura_od`, `ura_do`) in oznake izhajajo iz konstante,
  - stran učilnice prikaže datum, šolsko uro, čas in namen,
  - anonimni uporabnik je pri `/rezervacije/nova/` preusmerjen na prijavo,
  - uporabnik ne more preklicati tuje rezervacije (404),
  - prazen seznam učilnic prikaže sporočilo, fixture naloži 14 učilnic po oznaki,
  - koledar: zasedena ura ni klikljiva, prosta vodi na predizpolnjen obrazec (anonimne
    prek prijave), lastna rezervacija je označena, neveljaven `?teden=` prikaže privzeti teden,
  - obrazec nove rezervacije prevzame `ucilnica`, `datum` in `solska_ura` iz povezave.
