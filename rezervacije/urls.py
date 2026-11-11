from django.urls import path

from . import views

app_name = "rezervacije"

urlpatterns = [
    path("", views.UcilnicaListView.as_view(), name="ucilnica_list"),
    path("ucilnice/<int:pk>/", views.UcilnicaDetailView.as_view(), name="ucilnica_detail"),
    path("koledar/", views.KoledarView.as_view(), name="koledar"),
    path("rezervacije/nova/", views.RezervacijaCreateView.as_view(), name="nova"),
    path("rezervacije/moje/", views.MojeRezervacijeView.as_view(), name="moje"),
    path("rezervacije/<int:pk>/uredi/", views.RezervacijaUpdateView.as_view(), name="uredi"),
    path("rezervacije/<int:pk>/preklici/", views.RezervacijaDeleteView.as_view(), name="preklici"),
]
