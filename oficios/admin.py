from django.contrib import admin

from .models import Oficio


@admin.register(Oficio)
class OficioAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_do_oficio", "protocolo", "status", "data_criacao", "roteiro")
    search_fields = ("protocolo", "assunto", "motivo", "numero", "ano")
    list_filter = ("status", "custeio", "data_criacao")
    filter_horizontal = ("servidores",)

    @admin.display(description="N° do Ofício")
    def numero_do_oficio(self, obj):
        return obj.numero_formatado
