from django.contrib import admin
from .models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "bloco", "capacidade")
    search_fields = ("nome", "bloco")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "inscricoes_abertas", "organizador")
    list_filter = ("inscricoes_abertas",)
    search_fields = ("nome",)


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "evento", "tipo", "sala", "inicio", "fim")
    list_filter = ("tipo", "evento", "sala")
    search_fields = ("titulo",)


@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    list_display = ("participante", "evento", "data")
    list_filter = ("evento",)


@admin.register(InscricaoAtividade)
class InscricaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ("inscricao_evento", "atividade", "data")
    list_filter = ("atividade",)