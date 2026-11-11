from django.core.exceptions import ValidationError as ModelError
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Evento, Atividade, InscricaoEvento, InscricaoAtividade
from . import services


def executar(funcao, *args):
    try:
        return funcao(*args)
    except ModelError as erro:
        raise serializers.ValidationError(getattr(erro, 'message_dict', erro.messages))


class EventoPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = ['id', 'nome', 'descricao', 'data_inicio', 'data_fim', 'inscricoes_abertas']


class AtividadePublicaSerializer(serializers.ModelSerializer):
    sala = serializers.CharField(source='sala.nome', read_only=True)
    vagas_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Atividade
        fields = ['id', 'evento', 'titulo', 'tipo', 'descricao', 'responsavel', 'sala', 'inicio', 'fim', 'vagas_restantes']


class EventoGestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = ['id', 'nome', 'descricao', 'data_inicio', 'data_fim', 'inscricoes_abertas', 'organizador']
        read_only_fields = ['organizador']

    def validate(self, attrs):
        instancia = Evento()
        if self.instance:
            for campo in Evento._meta.fields:
                setattr(instancia, campo.attname, getattr(self.instance, campo.attname))
        for campo, valor in attrs.items():
            setattr(instancia, campo, valor)
        instancia.organizador = self.context['request'].user
        executar(instancia.full_clean)
        return attrs


class AtividadeGestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atividade
        fields = ['id', 'evento', 'titulo', 'tipo', 'descricao', 'responsavel', 'sala', 'inicio', 'fim']

    def validate(self, attrs):
        instancia = Atividade()
        if self.instance:
            for campo in Atividade._meta.fields:
                setattr(instancia, campo.attname, getattr(self.instance, campo.attname))
        for campo, valor in attrs.items():
            setattr(instancia, campo, valor)
        services.exigir_dono_evento(self.context['request'].user, instancia.evento)
        executar(instancia.full_clean)
        return attrs


class EventoPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = Evento.objects.all()
    serializer_class = EventoPublicoSerializer

    @action(detail=True, methods=['get'])
    def programacao(self, request, pk=None):
        evento = self.get_object()
        atividades = evento.atividades.select_related('sala').annotate(total_inscritos=Count('inscricoes'))
        return Response(AtividadePublicaSerializer(atividades, many=True).data)


class EventoGestaoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoGestaoSerializer

    def perform_create(self, serializer):
        if not services.eh_organizador(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas organizadores podem criar eventos.')
        serializer.save(organizador=self.request.user)

    def get_object(self):
        evento = super().get_object()
        services.exigir_dono_evento(self.request.user, evento)
        return evento


class AtividadeGestaoViewSet(viewsets.ModelViewSet):
    queryset = Atividade.objects.select_related('evento', 'sala')
    serializer_class = AtividadeGestaoSerializer

    def get_object(self):
        atividade = super().get_object()
        services.exigir_dono_evento(self.request.user, atividade.evento)
        return atividade


class InscricaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def evento(self, request, pk=None):
        inscricao = executar(services.inscrever_evento, request.user, get_object_or_404(Evento, pk=pk))
        return Response({'id': inscricao.pk}, status=201)

    @action(detail=True, methods=['post'])
    def atividade(self, request, pk=None):
        inscricao = executar(services.inscrever_atividade, request.user, get_object_or_404(Atividade, pk=pk))
        return Response({'id': inscricao.pk}, status=201)

    @action(detail=True, methods=['post'], url_path='cancelar-evento')
    def cancelar_evento(self, request, pk=None):
        executar(services.cancelar, request.user, get_object_or_404(InscricaoEvento, pk=pk))
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='cancelar-atividade')
    def cancelar_atividade(self, request, pk=None):
        executar(services.cancelar, request.user, get_object_or_404(InscricaoAtividade, pk=pk))
        return Response(status=204)
