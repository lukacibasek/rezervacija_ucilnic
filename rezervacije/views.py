from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RezervacijaForm
from .models import Rezervacija, Ucilnica


def prihodnje(queryset):
    """Rezervacije, ki se še niso končale."""
    zdaj = timezone.localtime()
    return queryset.filter(
        Q(datum__gt=zdaj.date()) | Q(datum=zdaj.date(), ura_do__gt=zdaj.time())
    )


class UcilnicaListView(ListView):
    model = Ucilnica
    ordering = ["oznaka"]
    context_object_name = "ucilnice"


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
