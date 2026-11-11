"""Regras usadas pelas duas portas. Não dependem de HTTP ou serializers."""
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from .models import Evento, Atividade, InscricaoEvento, InscricaoAtividade


def eh_organizador(user):
    return user.is_authenticated and user.groups.filter(name='Organizadores').exists()


def exigir_dono_evento(user, evento):
    if not eh_organizador(user) or evento.organizador_id != user.pk:  # DONO_EVENTO
        raise PermissionDenied('Você não é o organizador deste evento.')


@transaction.atomic
def inscrever_evento(user, evento):
    if not evento.inscricoes_abertas:
        raise ValidationError('Este evento não está mais aceitando inscrições.')
    if InscricaoEvento.objects.filter(evento=evento, participante=user).exists():
        raise ValidationError('Você já está inscrito neste evento.')
    return InscricaoEvento.objects.create(evento=evento, participante=user)


@transaction.atomic
def inscrever_atividade(user, atividade):
    atividade = Atividade.objects.select_for_update().select_related('sala', 'evento').get(pk=atividade.pk)
    inscricao = InscricaoEvento.objects.filter(evento=atividade.evento, participante=user).first()
    if inscricao is None:  # RN4_EVENTO
        raise ValidationError('Você precisa estar inscrito no evento primeiro.')
    if atividade.inscricoes.count() >= atividade.sala.capacidade:  # RN1_CAPACIDADE
        raise ValidationError('Esta atividade está lotada.')
    if InscricaoAtividade.objects.filter(inscricao_evento=inscricao, atividade=atividade).exists():
        raise ValidationError('Você já está inscrito nesta atividade.')
    conflito = Atividade.objects.filter(inscricoes__inscricao_evento__participante=user,
        inicio__lt=atividade.fim, fim__gt=atividade.inicio).exists()
    if conflito:  # RN2_HORARIO
        raise ValidationError('Esta atividade conflita com outra em que você já está inscrito.')
    return InscricaoAtividade.objects.create(inscricao_evento=inscricao, atividade=atividade)


def exigir_dono_inscricao(user, inscricao):
    dono = inscricao.participante_id if isinstance(inscricao, InscricaoEvento) else inscricao.inscricao_evento.participante_id
    if dono != user.pk:
        raise PermissionDenied('Você só pode cancelar suas próprias inscrições.')


@transaction.atomic
def cancelar(user, inscricao):
    exigir_dono_inscricao(user, inscricao)
    inscricao.delete()  # RN5_CASCATA (ForeignKey CASCADE no model)
