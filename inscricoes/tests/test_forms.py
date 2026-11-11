from .base import Cenario
from inscricoes.views import EventoForm


class FormulariosTests(Cenario):
    def dados(self):
        return {'nome': 'Encontro', 'descricao': 'Pesquisa', 'data_inicio': self.evento.data_inicio,
            'data_fim': self.evento.data_fim, 'inscricoes_abertas': True}

    def test_formulario_valido_limpa_os_dados(self):
        form = EventoForm(data=self.dados())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data['nome'], 'Encontro')
        self.assertEqual(form.cleaned_data['data_inicio'], self.evento.data_inicio)

    def test_formulario_invalido_informa_campo_obrigatorio(self):
        form = EventoForm(data={**self.dados(), 'nome': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertNotIn('nome', form.cleaned_data)
