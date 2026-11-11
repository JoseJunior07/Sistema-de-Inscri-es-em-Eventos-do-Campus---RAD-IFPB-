# Sistema de Inscrições em Eventos do Campus — Atividade 08

**Integrante: José Correia da Cruz Júnior**

Projeto Django com site HTML e API REST. A atividade 08 acrescenta testes automatizados e evidências de nove sabotagens. O ramo `atividade-08-testes` preserva o `main` original.

## Ponto de partida e ajustes necessários

O projeto recebido tinha as telas HTML, mas ainda não tinha API REST ou testes. Primeiro foi preparada a API com Django REST Framework, requisito de entrada da atividade. A única ferramenta nova de testes é `coverage`; o executor continua sendo o padrão do Django. Também foram acrescentadas validações de datas nos models para permitir `full_clean()`.

As regras de sala ocupada e período da atividade estavam repetidas em `criar_atividade` e `editar_atividade`. Foram centralizadas em `Atividade.clean()`, chamado tanto pelo ModelForm quanto pelo serializer. Inscrição prévia, capacidade e conflito do participante passaram das views para `services.py`, compartilhado com a API. O cancelamento também usa um serviço único, e a exclusão em cascata continua a cargo da ForeignKey com CASCADE. A verificação de dono é compartilhada.

A programação já usava `select_related('sala')`, mas calculava vagas com uma consulta por atividade. Agora usa também agregação de inscritos e carrega o organizador junto do evento. O teste comprova **duas consultas** tanto com uma quanto com nove atividades. Foi corrigido o cancelamento anônimo, que verificava o dono antes do redirecionamento ao login, e foram acrescentadas mensagens de sucesso às operações do site.

## Preparação no Windows 11

Use Python 3.13. No PowerShell:

```powershell
git clone --branch atividade-08-testes https://github.com/JoseJunior07/Sistema-de-Inscri-es-em-Eventos-do-Campus---RAD-IFPB-.git
cd Sistema-de-Inscri-es-em-Eventos-do-Campus---RAD-IFPB-
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Não é necessário ativar o ambiente ou alterar a política do PowerShell. Nos comandos seguintes, substitua `python` por `.\.venv\Scripts\python.exe` se não tiver ativado o ambiente.

## Preparação no Linux

Com Python 3.10 ou superior e Git instalados (em Ubuntu/Debian, instale também `python3-venv`):

```bash
git clone --branch atividade-08-testes https://github.com/JoseJunior07/Sistema-de-Inscri-es-em-Eventos-do-Campus---RAD-IFPB-.git
cd Sistema-de-Inscri-es-em-Eventos-do-Campus---RAD-IFPB-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse o site em <http://127.0.0.1:8000/>. As telas continuam sendo templates Django; nesta atividade isso é exigido, diferentemente do catálogo de TCCs. Os testes foram executados no Windows, com Python 3.13.5 e Django 5.2.19. O procedimento Linux está documentado, mas não foi executado nesta máquina.

## Como rodar a suíte

Execute na pasta de `manage.py`:

```bash
python manage.py test
python manage.py test --shuffle=11
python manage.py test --shuffle=22
python manage.py test --shuffle=33
python manage.py test inscricoes.tests.test_models
python manage.py test -v 2
```

A suíte final tem **47 testes**, nenhum pulado. A execução com shuffle 11 levou **5,586 segundos no runner** (7,517 segundos incluindo inicialização e encerramento). Com coverage, o runner levou 12,015 segundos. Tempos variam entre máquinas. Os três shuffles passaram. Os seis testes de models passaram isoladamente. A suíte também passou com o banco de desenvolvimento temporariamente retirado da pasta e restaurado em seguida. Nenhum teste lê os registros do `db.sqlite3` entregue: os cenários são criados por `setUpTestData`.

O pacote `inscricoes/tests/` separa models, formulários, views e API. O antigo `inscricoes/tests.py` foi removido. `regras.py` define dez cenários, executados por duas classes: uma chama o site por sessão e outra chama a API com token real. São **20 testes das cinco regras**, com caminhos aceitos e recusados em ambas as portas. Endereços nos testes são obtidos com `reverse()`. Não há `sleep` nem testes pulados.

Os demais testes cobrem conteúdo/contexto/template, POST com efeito no banco, mensagens e redirect, autenticação com `next`, autorizações com conferência do banco intacto, formulário direto com `is_valid`, `errors` e `cleaned_data`, contrato público, token e consultas constantes.

## Cobertura

```bash
python -m coverage run manage.py test
python -m coverage report
python -m coverage html
```

**Cobertura de linhas: 88%**, com 354 de 401 instruções cobertas (47 não cobertas). Escopo: app `inscricoes`, excluindo migrations e testes, conforme `.coveragerc`. Models: 93%; serviços: 92%; API: 89%; views: 81%. O relatório detalhado está em `evidencias/coverage-report.txt` e o JSON em `evidencias/coverage.json`.

Esse percentual mede linhas executadas, não a qualidade das asserções. A sabotagem 8 ficou verde na primeira rodada: os testes conferiam os dados presentes, mas não percebiam um campo privado a mais. Foi necessário acrescentar uma asserção do conjunto exato de campos da lista e do detalhe. Depois disso, a mesma sabotagem falhou. Assim, mesmo uma suíte com cobertura elevada pode deixar passar uma quebra de contrato; as linhas ainda não cobertas e os comportamentos fora dos cenários também merecem novos testes.

## Tabela de sabotagem — resultados reais

Cada alteração foi aplicada isoladamente, a suíte inteira foi executada e o código original foi restaurado em `finally`. A primeira rodada tinha 46 testes; o teste acrescentado após a sabotagem 8 elevou o total para 47.

| Sabotagem | Teste que falhou | Verde na 1ª rodada? |
| --- | --- | --- |
| 1. Capacidade da sala | `test_capacidade_recusa_sala_lotada` | Não |
| 2. Horário do participante | `test_horario_recusa_atividades_sobrepostas` | Não |
| 3. Sala ocupada | `test_sala_recusa_atividades_sobrepostas` | Não |
| 4. Inscrição prévia no evento | `test_evento_recusa_atividade_sem_inscricao_previa` | Não |
| 5. Cancelamento em cascata | `test_cancelamento_post_banco_redirect_e_mensagem`; `test_cancelamento_remove_atividades_do_evento` | Não |
| 6. Render após POST | `test_inscricao_post_banco_redirect_e_mensagem` | Não |
| 7. Dono do evento | `test_organizador_alheio_nao_edita`; `test_organizador_nao_edita_evento_alheio_banco_intacto` | Não |
| 8. Campo privado no serializer público | Nenhum na primeira rodada. Depois: `test_publico_expoe_somente_campos_do_contrato` | Sim |
| 9. Select related da programação | `test_programacao_numero_consultas_constante_com_mais_atividades` | Não |

Para as regras 1 a 5, os nomes de cenários citados aparecem tanto em `RegrasHTMLTests` quanto em `RegrasAPITests`, conforme os logs. A sabotagem 7 falhou nos testes HTML e API de dono. A sabotagem 8 foi repetida após o novo teste: o log original verde está em `evidencias/sabotagem-8-primeira-rodada.txt`, e o log corrigido está em `evidencias/sabotagem-8.txt`. Os JSONs registram os nomes completos dos testes, tempos, códigos de saída e substituições exatas.

Detalhes das mutações: 1 e 2 desativam seus `if`; 3 desativa a recusa por sala; 4 troca a recusa sem inscrição prévia por inscrição automática; 5 suprime a chamada `delete()` responsável por disparar a cascata (a operação inteira deixa de excluir, inclusive as atividades); 6 troca redirect por render; 7 remove apenas a comparação do organizador dono; 8 acrescenta `organizador` ao serializer público; 9 remove o `select_related('sala')` da programação.

Para reproduzir uma sabotagem:

```bash
python verificar_sabotagens.py 3
python manage.py test
```

O primeiro comando executa o runner Django sobre o código temporariamente quebrado e grava o resultado; o segundo deve passar com o código restaurado. O script de automação termina normalmente mesmo quando a suíte sabotada falha: consulte o `exit_code` e `falhas` impressos e o log. Sem número, ele repete as nove mutações. Não execute o script ao mesmo tempo que edita os mesmos fontes. Os desafios opcionais não foram incluídos.

## API adicionada como pré-requisito

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/api/publico/eventos/` | Lista de eventos sem token |
| GET | `/api/publico/eventos/{id}/` | Detalhe público |
| GET | `/api/publico/eventos/{id}/programacao/` | Programação sem dados de inscritos |
| POST | `/api/token/` | Receber token por usuário e senha |
| GET, POST | `/api/gestao/eventos/` | Gestão pelo organizador |
| GET, PUT, PATCH, DELETE | `/api/gestao/eventos/{id}/` | Apenas organizador dono |
| GET, POST | `/api/gestao/atividades/` | Atividades com validação do dono |
| GET, PUT, PATCH, DELETE | `/api/gestao/atividades/{id}/` | Apenas dono do evento |
| POST | `/api/gestao/inscricoes/{evento_id}/evento/` | Inscrever o usuário do token no evento |
| POST | `/api/gestao/inscricoes/{atividade_id}/atividade/` | Inscrever o usuário do token na atividade |
| POST | `/api/gestao/inscricoes/{inscricao_id}/cancelar-evento/` | Cancelar inscrição própria no evento |
| POST | `/api/gestao/inscricoes/{inscricao_id}/cancelar-atividade/` | Cancelar inscrição própria na atividade |

Listas da gestão são autenticadas; as mutações de evento/atividade exigem organizador dono. As operações de inscrição exigem usuário autenticado e o cancelamento exige o dono da inscrição. Sem token: 401. Autenticado sem permissão: 403. Validação de dados ou regras: 400 com JSON. Leitura pública usa serializer próprio, sem organizador, senhas, e-mails ou inscrições individuais.

Obtenha token com POST de `username` e `password` para `/api/token/` e envie `Authorization: Token VALOR` nas operações protegidas. Os testes não usam as contas abaixo nem `force_authenticate`: geram seus usuários e enviam tokens no cabeçalho.

## Contas e chave de execução

As senhas de contas do banco de demonstração não são publicadas neste README. Para preparar contas locais, use `python manage.py createsuperuser` e o Django Admin; associe os organizadores ao grupo `Organizadores`. Execute `migrate` antes de obter tokens pelo endpoint.

A chave do Django é lida de `DJANGO_SECRET_KEY`. Se ela não estiver definida, será gerada uma chave temporária para o processo, adequada para esta demonstração local. Nesse modo, reiniciar o servidor invalida sessões anteriores. Para sessões persistentes, defina uma chave pessoal na variável de ambiente, mantenha-a no computador e não a envie ao GitHub. As senhas usadas pelos testes são exclusivamente de usuários temporários, criados no banco de testes e descartados ao final.

## Evidências e explicação

- `evidencias/sabotagem-*.txt`: saídas completas das suítes sabotadas.
- `evidencias/resultado-*.json`: resumo legível por programa das rodadas.
- `evidencias/shuffle-*.txt`: três ordens diferentes com todos os testes passando.
- `evidencias/sem-banco-desenvolvimento.txt`: suíte independente do banco local.
- `evidencias/models-isolados.txt`: testes de models isolados.
- `evidencias/coverage-execucao.txt` e `coverage-report.txt`: execução e medição final.
- `LEIA-ME-ATIVIDADE08.md`: explicação do fluxo e roteiro para estudar a apresentação.

Entrega: link deste ramo público no Google Sala de Aula, ou integração do ramo ao principal antes de enviar o link principal. Reproduza ao menos uma sabotagem e entenda suas asserções antes da avaliação.

Referências: [testes Django](https://docs.djangoproject.com/en/5.2/topics/testing/overview/) e [testes DRF](https://www.django-rest-framework.org/api-guide/testing/).
