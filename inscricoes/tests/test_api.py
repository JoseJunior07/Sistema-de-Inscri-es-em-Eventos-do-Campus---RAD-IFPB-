from django.urls import reverse
from .base import Cenario
from .regras import RegrasCompartilhadas
from inscricoes.models import Evento, InscricaoAtividade


class RegrasAPITests(RegrasCompartilhadas, Cenario):
    api = True


class APITests(Cenario):
    def test_publico_expoe_somente_campos_do_contrato(self):
        client = self.cliente_api()
        campos = {'id', 'nome', 'descricao', 'data_inicio', 'data_fim', 'inscricoes_abertas'}
        lista = client.get(reverse('api-publico-evento-list'))
        detalhe = client.get(reverse('api-publico-evento-detail', args=[self.evento.pk]))
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(set(lista.data[0]), campos)
        self.assertEqual(set(detalhe.data), campos)
        self.assertNotIn('organizador', detalhe.data)

    def dados_evento(self):
        return {'nome': 'Novo evento', 'descricao': 'Pesquisa', 'data_inicio': self.evento.data_inicio.isoformat(),
            'data_fim': self.evento.data_fim.isoformat(), 'inscricoes_abertas': True}

    def test_publico_lista_e_programacao_sem_token(self):
        client = self.cliente_api()
        r = client.get(reverse('api-publico-evento-list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]['nome'], self.evento.nome)
        r = client.get(reverse('api-publico-evento-programacao', args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]['titulo'], self.atividade.titulo)
        self.assertEqual(r.data[0]['sala'], self.sala.nome)

    def test_sem_token_401_banco_intacto(self):
        r = self.cliente_api().post(reverse('api-gestao-evento-list'), self.dados_evento(), format='json')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(Evento.objects.count(), 1)

    def test_token_participante_403_banco_intacto(self):
        r = self.cliente_api(self.pessoa).post(reverse('api-gestao-evento-list'), self.dados_evento(), format='json')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Evento.objects.count(), 1)

    def test_token_organizador_cria_evento(self):
        r = self.cliente_api(self.org).post(reverse('api-gestao-evento-list'), self.dados_evento(), format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Evento.objects.get(pk=r.data['id']).organizador, self.org)

    def test_organizador_alheio_nao_edita(self):
        r = self.cliente_api(self.outro_org).patch(reverse('api-gestao-evento-detail', args=[self.evento.pk]), {'nome': 'Invasão'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.nome, 'Semana Acadêmica')

    def test_token_obtido_por_usuario_e_senha(self):
        r = self.cliente_api().post(reverse('api-token'), {'username': 'organizador', 'password': 'senha-teste'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['token'])

    def test_nao_cancela_atividade_alheia(self):
        ia = InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(self.outra), atividade=self.atividade)
        r = self.cliente_api(self.pessoa).post(reverse('api-inscricao-cancelar-atividade', args=[ia.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(InscricaoAtividade.objects.filter(pk=ia.pk).exists())
