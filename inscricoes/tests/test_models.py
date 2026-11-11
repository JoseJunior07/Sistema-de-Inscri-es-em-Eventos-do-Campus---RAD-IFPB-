from datetime import timedelta
from django.core.exceptions import ValidationError
from .base import Cenario
from inscricoes.models import Sala


class ModelsTests(Cenario):
    def test_evento_recusa_fim_antes_do_inicio(self):
        self.evento.data_fim = self.evento.data_inicio - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.evento.full_clean()

    def test_atividade_recusa_fim_antes_do_inicio(self):
        self.atividade.fim = self.atividade.inicio - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.atividade.full_clean()

    def test_sala_recusa_capacidade_negativa(self):
        self.sala.capacidade = -1
        with self.assertRaises(ValidationError):
            self.sala.full_clean()

    def test_evento_recusa_nome_vazio(self):
        self.evento.nome = ''
        with self.assertRaises(ValidationError):
            self.evento.full_clean()

    def test_dados_validos_passam_full_clean(self):
        self.sala.full_clean()
        self.evento.full_clean()
        self.atividade.full_clean()

    def test_vagas_restantes_confere_valor(self):
        from inscricoes.models import InscricaoAtividade
        self.assertEqual(self.atividade.vagas_restantes(), 1)
        InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(), atividade=self.atividade)
        self.assertEqual(self.atividade.vagas_restantes(), 0)
