from django.urls import path
from . import views

app_name = 'contratos'

urlpatterns = [
    path('', views.ContratoListView.as_view(), name='lista'),
    path('novo/', views.contrato_novo, name='novo'),
    path('<uuid:pk>/', views.contrato_detalhe, name='detalhe'),
    path('<uuid:pk>/renovar/', views.contrato_renovar, name='renovar'),
]
