from datetime import timedelta
from django.urls import reverse
from inscricoes.models import InscricaoAtividade, InscricaoEvento, Atividade


class RegrasCompartilhadas:
    """Cada cenário é executado por uma classe HTML e por outra API."""
    api = False

    def setUp(self):
        super().setUp()
        self.client.force_login(self.pessoa)
        self.api_client = self.cliente_api(self.pessoa)

    def participar(self, atividade):
        if self.api:
            return self.api_client.post(reverse('api-inscricao-atividade', args=[atividade.pk]))
        return self.client.post(reverse('inscrever_atividade', args=[atividade.pk]))

    def cancelar_evento(self, inscricao):
        if self.api:
            return self.api_client.post(reverse('api-inscricao-cancelar-evento', args=[inscricao.pk]))
        return self.client.post(reverse('cancelar_evento', args=[inscricao.pk]))

    def criar_atividade(self, inicio):
        dados = {'titulo': 'Nova oficina', 'tipo': 'TR', 'descricao': '', 'responsavel': 'Ana',
            'sala': self.sala.pk, 'inicio': inicio.isoformat(), 'fim': (inicio + timedelta(hours=1)).isoformat()}
        if self.api:
            return self.cliente_api(self.org).post(reverse('api-gestao-atividade-list'), {**dados, 'evento': self.evento.pk}, format='json')
        self.client.force_login(self.org)
        return self.client.post(reverse('criar_atividade', args=[self.evento.pk]), dados)

    def test_capacidade_permite_inscricao_com_vaga(self):
        self.inscricao()
        r = self.participar(self.atividade)
        self.assertEqual(r.status_code, 201 if self.api else 302)
        self.assertEqual(InscricaoAtividade.objects.filter(atividade=self.atividade).count(), 1)

    def test_capacidade_recusa_sala_lotada(self):
        InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(self.outra), atividade=self.atividade)
        self.inscricao()
        r = self.participar(self.atividade)
        self.assertEqual(r.status_code, 400 if self.api else 302)
        self.assertFalse(InscricaoAtividade.objects.filter(inscricao_evento__participante=self.pessoa).exists())

    def test_horario_permite_atividades_consecutivas(self):
        InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(), atividade=self.atividade)
        r = self.participar(self.segunda_atividade())
        self.assertEqual(r.status_code, 201 if self.api else 302)
        self.assertEqual(InscricaoAtividade.objects.filter(inscricao_evento__participante=self.pessoa).count(), 2)

    def test_horario_recusa_atividades_sobrepostas(self):
        InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(), atividade=self.atividade)
        alvo = self.segunda_atividade(sobreposta=True)
        r = self.participar(alvo)
        self.assertEqual(r.status_code, 400 if self.api else 302)
        self.assertFalse(InscricaoAtividade.objects.filter(atividade=alvo).exists())

    def test_sala_permite_atividades_consecutivas(self):
        r = self.criar_atividade(self.atividade.fim)
        self.assertEqual(r.status_code, 201 if self.api else 302)
        self.assertEqual(Atividade.objects.count(), 2)

    def test_sala_recusa_atividades_sobrepostas(self):
        r = self.criar_atividade(self.inicio + timedelta(minutes=30))
        self.assertEqual(r.status_code, 400 if self.api else 200)
        self.assertEqual(Atividade.objects.count(), 1)

    def test_evento_permite_atividade_com_inscricao_previa(self):
        self.inscricao()
        self.participar(self.atividade)
        self.assertTrue(InscricaoAtividade.objects.filter(inscricao_evento__participante=self.pessoa).exists())

    def test_evento_recusa_atividade_sem_inscricao_previa(self):
        r = self.participar(self.atividade)
        self.assertEqual(r.status_code, 400 if self.api else 403)
        self.assertFalse(InscricaoAtividade.objects.exists())
        self.assertFalse(InscricaoEvento.objects.exists())

    def test_cancelamento_remove_atividades_do_evento(self):
        ie = self.inscricao()
        InscricaoAtividade.objects.create(inscricao_evento=ie, atividade=self.atividade)
        r = self.cancelar_evento(ie)
        self.assertEqual(r.status_code, 204 if self.api else 302)
        self.assertFalse(InscricaoAtividade.objects.exists())
        self.assertFalse(InscricaoEvento.objects.filter(pk=ie.pk).exists())

    def test_cancelamento_recusa_inscricao_de_outra_pessoa(self):
        ie = self.inscricao(self.outra)
        ia = InscricaoAtividade.objects.create(inscricao_evento=ie, atividade=self.atividade)
        r = self.cancelar_evento(ie)
        self.assertEqual(r.status_code, 403)
        self.assertTrue(InscricaoEvento.objects.filter(pk=ie.pk).exists())
        self.assertTrue(InscricaoAtividade.objects.filter(pk=ia.pk).exists())
