from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.ClienteListView.as_view(), name="lista"),
    path("novo/", views.cliente_novo, name="novo"),
    path("<uuid:pk>/", views.cliente_detalhe, name="detalhe"),
    path("<uuid:pk>/editar/", views.cliente_editar, name="editar"),
]