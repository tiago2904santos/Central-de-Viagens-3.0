from django.contrib import admin

from .models import Oficio


@admin.register(Oficio)
class OficioAdmin(admin.ModelAdmin):
    list_display = ("id", "numero", "ano", "protocolo", "status", "data_criacao", "roteiro")
    search_fields = ("protocolo", "assunto", "motivo", "numero", "ano")
    list_filter = ("status", "custeio", "data_criacao")
    filter_horizontal = ("servidores",)
