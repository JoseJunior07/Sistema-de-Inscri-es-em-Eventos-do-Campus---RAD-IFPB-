"""Executa uma mutação por vez, restaura os fontes e guarda a saída real do runner.

Uso: python verificar_sabotagens.py [1 2 ... 9]
Não executar simultaneamente com outro processo que edite estes mesmos arquivos.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASOS = [
    (1, 'Capacidade da sala', 'inscricoes/services.py',
     'if atividade.inscricoes.count() >= atividade.sala.capacidade:  # RN1_CAPACIDADE',
     'if False:  # RN1_CAPACIDADE'),
    (2, 'Horário do participante', 'inscricoes/services.py',
     'if conflito:  # RN2_HORARIO', 'if False:  # RN2_HORARIO'),
    (3, 'Sala ocupada', 'inscricoes/models.py',
     'if conflito.exists():  # RN3_SALA', 'if False:  # RN3_SALA'),
    (4, 'Inscrição prévia no evento', 'inscricoes/services.py',
     "if inscricao is None:  # RN4_EVENTO\n        raise ValidationError('Você precisa estar inscrito no evento primeiro.')",
     "if inscricao is None:  # RN4_EVENTO sabotada: aceita inscrição implícita\n        inscricao = InscricaoEvento.objects.create(evento=atividade.evento, participante=user)"),
    (5, 'Cancelamento em cascata', 'inscricoes/services.py',
     'inscricao.delete()  # RN5_CASCATA (ForeignKey CASCADE no model)',
     'return  # RN5_CASCATA: não aciona a exclusão e sua cascata'),
    (6, 'Render após POST', 'inscricoes/views.py',
     "return redirect('detalhe_evento', pk=pk)  # POST_REDIRECT",
     'return render(request, "inscricoes/detalhe_evento.html", {"evento": evento, "atividades": []})  # POST_REDIRECT'),
    (7, 'Dono do evento', 'inscricoes/services.py',
     'if not eh_organizador(user) or evento.organizador_id != user.pk:  # DONO_EVENTO',
     'if not eh_organizador(user):  # DONO_EVENTO sem comparação de dono'),
    (8, 'Campo privado no serializer público', 'inscricoes/api.py',
     "fields = ['id', 'nome', 'descricao', 'data_inicio', 'data_fim', 'inscricoes_abertas']",
     "fields = ['id', 'nome', 'descricao', 'data_inicio', 'data_fim', 'inscricoes_abertas', 'organizador']"),
    (9, 'Select related da programação', 'inscricoes/views.py',
     'evento.atividades.select_related("sala").annotate', 'evento.atividades.all().annotate'),
]


def main():
    selecionados = set(map(int, sys.argv[1:])) if sys.argv[1:] else set(range(1, 10))
    pasta = ROOT / 'evidencias'
    pasta.mkdir(exist_ok=True)
    resultados = []
    for numero, nome, arquivo, antes, depois in CASOS:
        if numero not in selecionados:
            continue
        caminho = ROOT / arquivo
        original = caminho.read_text(encoding='utf-8')
        if original.count(antes) != 1:
            raise RuntimeError(f'Marcador ambíguo ou ausente na sabotagem {numero}')
        inicio = time.perf_counter()
        try:
            caminho.write_text(original.replace(antes, depois, 1), encoding='utf-8')
            processo = subprocess.run([sys.executable, '-B', 'manage.py', 'test', '-v', '2', '--noinput'],
                cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        finally:
            caminho.write_text(original, encoding='utf-8')
        saida = processo.stdout + '\n' + processo.stderr
        (pasta / f'sabotagem-{numero}.txt').write_text(saida, encoding='utf-8')
        falhas = re.findall(r'^(?:FAIL|ERROR): (.+)$', saida, re.MULTILINE)
        resultado = {'numero': numero, 'nome': nome, 'exit_code': processo.returncode,
                     'segundos': round(time.perf_counter()-inicio, 3), 'falhas': falhas,
                     'arquivo': arquivo, 'antes': antes, 'depois': depois}
        resultados.append(resultado)
        print(json.dumps(resultado, ensure_ascii=False), flush=True)
    (pasta / ('resultado-' + '-'.join(str(r['numero']) for r in resultados) + '.json')).write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
