from django.urls import path
from . import views

app_name = 'mensalidades'

urlpatterns = [
    path('', views.MensalidadeListView.as_view(), name='lista'),
    path('<uuid:pk>/', views.mensalidade_detalhe, name='detalhe'),
    path('<uuid:pk>/pagar/', views.registrar_pagamento, name='pagar'),
    path('<uuid:pk>/observacao/', views.salvar_observacao, name='observacao'),
]
