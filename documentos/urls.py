from django.urls import path

from . import views


app_name = "documentos"

urlpatterns = [
    path("", views.index, name="index"),
    path("artefatos/<uuid:pk>/assinar/", views.assinar_artefato_documento, name="assinar_artefato"),
]
