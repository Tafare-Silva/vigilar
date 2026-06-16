from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("apps.dashboard.urls", namespace="dashboard")),
    path("clientes/", include("apps.clientes.urls", namespace="clientes")),
    path("fornecedores/", include("apps.fornecedores.urls", namespace="fornecedores")),
    path("servicos/", include("apps.servicos.urls", namespace="servicos")),
    path("contratos/", include("apps.contratos.urls", namespace="contratos")),
    path("mensalidades/", include("apps.mensalidades.urls", namespace="mensalidades")),
    path("boletos/", include("apps.boletos.urls", namespace="boletos")),
    path("rondas/", include("apps.rondas.urls", namespace="rondas")),
    path("configuracoes/", include("apps.core.urls", namespace="configuracoes")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/clientes/", include("apps.clientes.urls_api", namespace="api-clientes")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
