from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

app_name = "fornecedores"

urlpatterns = [
    path("", login_required(TemplateView.as_view(template_name="core/em_breve.html")), name="lista"),
]
