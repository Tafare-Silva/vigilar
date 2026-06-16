from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    path('', views.ServicoListView.as_view(), name='lista'),
    path('novo/', views.servico_novo, name='novo'),
    path('<uuid:pk>/editar/', views.servico_editar, name='editar'),
    path('<uuid:pk>/toggle/', views.servico_toggle_ativo, name='toggle'),
]
