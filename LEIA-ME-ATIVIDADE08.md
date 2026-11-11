# Como estudar e demonstrar a atividade 08

Este projeto começou com site HTML, mas não tinha API REST. A API foi preparada antes da etapa de testes. O histórico do Git preserva a versão anterior e o trabalho da atividade está no ramo `atividade-08-testes`.

## Caminho de uma inscrição

1. Site: a view recebe o POST, identifica o usuário pela sessão e chama `services.inscrever_atividade`.
2. API: o endpoint recebe o POST, identifica o usuário pelo cabeçalho de token e chama a mesma função.
3. O serviço confere inscrição no evento, capacidade e conflito de horário.
4. Se tudo estiver correto, cria a inscrição no banco. Caso contrário, levanta `ValidationError`.
5. O site apresenta a mensagem; a API transforma a exceção em JSON com status 400.

Para atividades, a validação de sala ocupada está em `Atividade.clean()`, usada pelo ModelForm e pelo serializer. As datas de evento são validadas em `Evento.clean()`.

## O que cada arquivo de teste prova

- `test_models.py`: `full_clean()` recusa dados inválidos e o cálculo de vagas devolve o valor correto.
- `test_forms.py`: um formulário pode ser verificado diretamente, sem navegador ou view.
- `test_views.py`: regras pelo site, template, contexto, mensagens, redirecionamentos, dono e número de consultas.
- `test_api.py`: regras pelo token, resposta pública, autenticação e permissões.
- `regras.py`: cenários reaproveitados pelas classes HTML e API. Cada método é executado duas vezes, por clientes diferentes.
- `base.py`: cria o cenário comum com `setUpTestData`; não lê contas ou eventos do banco de desenvolvimento.

## Asserção é diferente de executar código

Chamar `atividade.vagas_restantes()` só prova que a chamada não levantou uma exceção. Já `assertEqual(atividade.vagas_restantes(), 0)` prova que a resposta foi zero naquele cenário. As sabotagens verificam se as asserções realmente percebem uma implementação quebrada.

## Cuidados para a apresentação

- Escolha uma sabotagem no README e execute `python verificar_sabotagens.py NUMERO`. O processo deve falhar nos testes descritos e restaurar o código ao final.
- Execute `python manage.py test` em seguida: o projeto restaurado deve passar.
- Explique a linha da tabela que ficou verde na primeira rodada e o teste acrescentado depois.
- Mostre a diferença entre 401 (sem identificação) e 403 (identificado, mas sem permissão).
- Mostre que os testes verificam o banco depois de uma recusa: retornar 403 e alterar os dados mesmo assim seria um erro.
- O teste de consultas verifica duas consultas tanto com uma quanto com nove atividades. A contagem não deve crescer junto com a lista.

As saídas guardadas são resultados de execuções reais, mas é importante reproduzi-las no seu computador e entender por que cada teste falhou. Tempos podem variar entre máquinas.
