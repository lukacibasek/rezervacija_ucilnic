from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RezervacijaForm
from .models import SOLSKE_URE, Rezervacija, Ucilnica


def prihodnje(queryset):
    """Rezervacije, ki se še niso končale."""
    zdaj = timezone.localtime()
    se_trajajo = [st for st, (_, konec) in SOLSKE_URE.items() if konec > zdaj.time()]
    return queryset.filter(
        Q(datum__gt=zdaj.date()) | Q(datum=zdaj.date(), solska_ura__in=se_trajajo)
    )


class UcilnicaListView(ListView):
    model = Ucilnica
    ordering = ["oznaka"]
    context_object_name = "ucilnice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["st_ucilnic"] = Ucilnica.objects.count()
        context["st_danes"] = Rezervacija.objects.filter(datum=timezone.localdate()).count()
        context["st_prihodnjih"] = prihodnje(Rezervacija.objects.all()).count()
        return context


class UcilnicaDetailView(DetailView):
    model = Ucilnica
    context_object_name = "ucilnica"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rezervacije"] = prihodnje(
            self.object.rezervacije.select_related("uporabnik")
        )
        return context


class RezervacijaCreateView(LoginRequiredMixin, CreateView):
    model = Rezervacija
    form_class = RezervacijaForm
    success_url = reverse_lazy("rezervacije:moje")

    def get_initial(self):
        """Predizpolni obrazec iz ?ucilnica=&datum=&solska_ura= (neveljavne vrednosti prezre)."""
        initial = super().get_initial()
        get = self.request.GET
        try:
            initial["ucilnica"] = Ucilnica.objects.get(pk=int(get["ucilnica"]))
        except (KeyError, ValueError, Ucilnica.DoesNotExist):
            pass
        try:
            initial["datum"] = date.fromisoformat(get["datum"])
        except (KeyError, ValueError):
            pass
        try:
            ura = int(get["solska_ura"])
            if ura in SOLSKE_URE:
                initial["solska_ura"] = ura
        except (KeyError, ValueError):
            pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Uporabnika nastavimo pred validacijo, da model.clean() dobi popoln objekt.
        form.instance.uporabnik = self.request.user
        return form

    def form_valid(self, form):
        messages.success(self.request, "Rezervacija je bila uspešno ustvarjena.")
        return super().form_valid(form)


class LastnikMixin(LoginRequiredMixin):
    """Dovoli dostop samo do rezervacij prijavljenega uporabnika (sicer 404)."""

    model = Rezervacija

    def get_queryset(self):
        return Rezervacija.objects.filter(uporabnik=self.request.user)


class MojeRezervacijeView(LastnikMixin, ListView):
    template_name = "rezervacije/moje_rezervacije.html"
    context_object_name = "rezervacije"

    def get_queryset(self):
        return super().get_queryset().select_related("ucilnica")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["danes"] = timezone.localdate()
        return context


class RezervacijaUpdateView(LastnikMixin, UpdateView):
    form_class = RezervacijaForm
    success_url = reverse_lazy("rezervacije:moje")

    def form_valid(self, form):
        messages.success(self.request, "Rezervacija je bila uspešno posodobljena.")
        return super().form_valid(form)


class RezervacijaDeleteView(LastnikMixin, DeleteView):
    success_url = reverse_lazy("rezervacije:moje")

    def form_valid(self, form):
        messages.success(self.request, "Rezervacija je bila preklicana.")
        return super().form_valid(form)
