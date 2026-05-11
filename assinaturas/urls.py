from django.urls import path

from . import views


app_name = "assinaturas"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/documentos/<uuid:pk>/verificar/", views.api_verificar_documento, name="api_verificar_documento"),
    path("api/documentos/<uuid:pk>/assinar/", views.api_assinar_documento, name="api_assinar_documento"),
]
