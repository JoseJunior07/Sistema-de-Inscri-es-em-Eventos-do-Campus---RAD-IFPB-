from datetime import timedelta
from django.urls import reverse
from django.contrib.messages import get_messages
from .base import Cenario
from .regras import RegrasCompartilhadas
from inscricoes.models import Evento, Atividade, InscricaoEvento, InscricaoAtividade


class RegrasHTMLTests(RegrasCompartilhadas, Cenario):
    pass


class ViewsTests(Cenario):
    def test_programacao_status_template_contexto_e_conteudo(self):
        r = self.client.get(reverse('detalhe_evento', args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'inscricoes/detalhe_evento.html')
        self.assertEqual(r.context['evento'], self.evento)
        self.assertEqual(list(r.context['atividades']), [self.atividade])
        self.assertContains(r, 'Palestra de abertura')
        self.assertContains(r, 'Semana Acadêmica')

    def test_programacao_numero_consultas_constante_com_mais_atividades(self):
        url = reverse('detalhe_evento', args=[self.evento.pk])
        with self.assertNumQueries(2):
            self.client.get(url)
        for i in range(1, 9):
            Atividade.objects.create(evento=self.evento, titulo=f'Oficina {i}', tipo='TR', responsavel='Ana',
                sala=self.sala2, inicio=self.inicio + timedelta(hours=i), fim=self.inicio + timedelta(hours=i+1))
        with self.assertNumQueries(2):
            self.client.get(url)

    def test_anonimo_redireciona_login_com_next(self):
        url = reverse('minha_agenda')
        r = self.client.get(url)
        self.assertRedirects(r, reverse('login') + '?next=' + url)

    def test_anonimo_cancelamento_redireciona_login_com_next(self):
        ie = self.inscricao()
        url = reverse('cancelar_evento', args=[ie.pk])
        self.assertRedirects(self.client.post(url), reverse('login') + '?next=' + url)
        self.assertTrue(InscricaoEvento.objects.filter(pk=ie.pk).exists())

    def test_inscricao_post_banco_redirect_e_mensagem(self):
        self.client.force_login(self.pessoa)
        r = self.client.post(reverse('inscrever_evento', args=[self.evento.pk]))
        self.assertRedirects(r, reverse('detalhe_evento', args=[self.evento.pk]))
        self.assertTrue(InscricaoEvento.objects.filter(evento=self.evento, participante=self.pessoa).exists())
        self.assertIn('Inscrição no evento realizada.', [str(m) for m in get_messages(r.wsgi_request)])

    def test_cancelamento_post_banco_redirect_e_mensagem(self):
        ie = self.inscricao()
        self.client.force_login(self.pessoa)
        r = self.client.post(reverse('cancelar_evento', args=[ie.pk]))
        self.assertRedirects(r, reverse('detalhe_evento', args=[self.evento.pk]))
        self.assertFalse(InscricaoEvento.objects.filter(pk=ie.pk).exists())
        self.assertIn('Inscrição cancelada.', [str(m) for m in get_messages(r.wsgi_request)])

    def test_participante_nao_cria_evento_banco_intacto(self):
        self.client.force_login(self.pessoa)
        self.assertEqual(self.client.post(reverse('criar_evento'), {'nome': 'Invasão'}).status_code, 403)
        self.assertEqual(Evento.objects.count(), 1)

    def test_participante_nao_edita_evento_banco_intacto(self):
        self.client.force_login(self.pessoa)
        self.assertEqual(self.client.post(reverse('editar_evento', args=[self.evento.pk]), {'nome': 'Invasão'}).status_code, 403)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.nome, 'Semana Acadêmica')

    def test_organizador_nao_edita_evento_alheio_banco_intacto(self):
        self.client.force_login(self.outro_org)
        dados = {'nome': 'Alterado', 'data_inicio': self.evento.data_inicio, 'data_fim': self.evento.data_fim, 'inscricoes_abertas': True}
        self.assertEqual(self.client.post(reverse('editar_evento', args=[self.evento.pk]), dados).status_code, 403)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.nome, 'Semana Acadêmica')

    def test_dono_edita_evento(self):
        self.client.force_login(self.org)
        r = self.client.post(reverse('editar_evento', args=[self.evento.pk]),
            {'nome': 'Alterado', 'data_inicio': self.evento.data_inicio, 'data_fim': self.evento.data_fim})
        self.assertEqual(r.status_code, 302)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.nome, 'Alterado')

    def test_nao_cancela_atividade_alheia(self):
        ia = InscricaoAtividade.objects.create(inscricao_evento=self.inscricao(self.outra), atividade=self.atividade)
        self.client.force_login(self.pessoa)
        self.assertEqual(self.client.post(reverse('cancelar_atividade', args=[ia.pk])).status_code, 403)
        self.assertTrue(InscricaoAtividade.objects.filter(pk=ia.pk).exists())
