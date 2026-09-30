from django.urls import path
from . import views

urlpatterns = [
    path("cadastro/", views.CadastroView.as_view(), name="cadastro"),
    path("", views.lista_eventos, name="lista_eventos"),
    path("eventos/<int:pk>/", views.detalhe_evento, name="detalhe_evento"),
    path("eventos/novo/", views.criar_evento, name="criar_evento"),
    path("eventos/<int:pk>/editar/", views.editar_evento, name="editar_evento"),
    path("eventos/<int:pk>/atividades/nova/", views.criar_atividade, name="criar_atividade"),
    path("eventos/<int:pk>/atividades/<int:atividade_pk>/editar/", views.editar_atividade, name="editar_atividade"),
    path("eventos/<int:pk>/inscrever/", views.inscrever_evento, name="inscrever_evento"),
    path("atividades/<int:pk>/inscrever/", views.inscrever_atividade, name="inscrever_atividade"),
    path("inscricoes-atividade/<int:pk>/cancelar/", views.CancelarAtividadeView.as_view(), name="cancelar_atividade"),
    path("inscricoes-evento/<int:pk>/cancelar/", views.CancelarEventoView.as_view(), name="cancelar_evento"),
    path("minha-agenda/", views.minha_agenda, name="minha_agenda"),
    path("eventos/<int:pk>/painel/", views.painel_organizador, name="painel_organizador"),
]