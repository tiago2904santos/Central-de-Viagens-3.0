from django.urls import path

from . import views


app_name = "assinaturas"

urlpatterns = [
    path("", views.index, name="index"),
    path("gestao/", views.assinatura_gestao, name="assinatura-gestao"),
    path("verificar/<str:codigo>/", views.assinatura_verificar_codigo, name="assinatura-verificar-codigo"),
    path("<uuid:assinatura_id>/pdf-original/", views.assinatura_pdf_original, name="assinatura-pdf-original"),
    path("<uuid:assinatura_id>/pdf-assinado/", views.assinatura_pdf_assinado, name="assinatura-pdf-assinado"),
    path("api/documentos/<uuid:pk>/verificar/", views.api_verificar_documento, name="api_verificar_documento"),
    path("api/documentos/<uuid:pk>/assinar/", views.api_assinar_documento, name="api_assinar_documento"),
]
