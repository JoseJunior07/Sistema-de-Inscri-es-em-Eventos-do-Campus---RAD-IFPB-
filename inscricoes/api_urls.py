from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .api import EventoPublicoViewSet, EventoGestaoViewSet, AtividadeGestaoViewSet, InscricaoViewSet

publico = DefaultRouter()
publico.register('eventos', EventoPublicoViewSet, basename='api-publico-evento')
gestao = DefaultRouter()
gestao.register('eventos', EventoGestaoViewSet, basename='api-gestao-evento')
gestao.register('atividades', AtividadeGestaoViewSet, basename='api-gestao-atividade')
gestao.register('inscricoes', InscricaoViewSet, basename='api-inscricao')
urlpatterns = [path('token/', obtain_auth_token, name='api-token'),
    path('publico/', include(publico.urls)), path('gestao/', include(gestao.urls))]
