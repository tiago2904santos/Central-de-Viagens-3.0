from django.urls import path

from . import views


app_name = "oficios"

urlpatterns = [
    path("", views.index, name="index"),
    path("novo/", views.novo, name="novo"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/dados-viajantes/", views.dados_viajantes, name="dados_viajantes"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
]
