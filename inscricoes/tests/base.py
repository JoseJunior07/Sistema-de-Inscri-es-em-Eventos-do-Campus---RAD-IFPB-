from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from inscricoes.models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade


class Cenario(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.org = User.objects.create_user('organizador', password='senha-teste')
        cls.outro_org = User.objects.create_user('outro-organizador')
        grupo = Group.objects.create(name='Organizadores')
        cls.org.groups.add(grupo)
        cls.outro_org.groups.add(grupo)
        cls.pessoa = User.objects.create_user('participante', password='senha-teste')
        cls.outra = User.objects.create_user('outra-pessoa')
        for user in [cls.org, cls.outro_org, cls.pessoa, cls.outra]:
            Token.objects.create(user=user)
        cls.inicio = make_aware(datetime(2026, 8, 10, 8))
        cls.sala = Sala.objects.create(nome='Sala A', bloco='A', capacidade=1)
        cls.sala2 = Sala.objects.create(nome='Sala B', bloco='B', capacidade=5)
        cls.evento = Evento.objects.create(nome='Semana Acadêmica', descricao='Conhecimento aberto',
            data_inicio=cls.inicio, data_fim=cls.inicio + timedelta(days=2), organizador=cls.org)
        cls.atividade = Atividade.objects.create(evento=cls.evento, titulo='Palestra de abertura', tipo='PA',
            responsavel='Ana', sala=cls.sala, inicio=cls.inicio, fim=cls.inicio + timedelta(hours=1))

    def inscricao(self, pessoa=None):
        return InscricaoEvento.objects.get_or_create(evento=self.evento, participante=pessoa or self.pessoa)[0]

    def segunda_atividade(self, sobreposta=False, mesma_sala=False):
        inicio = self.inicio if sobreposta else self.inicio + timedelta(hours=1)
        return Atividade.objects.create(evento=self.evento, titulo='Oficina', tipo='TR', responsavel='Bruno',
            sala=self.sala if mesma_sala else self.sala2, inicio=inicio, fim=inicio + timedelta(hours=1))

    def cliente_api(self, user=None):
        client = APIClient()
        if user:
            client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.get(user=user).key)
        return client
