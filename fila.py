"""Fila de lote que sobrevive a queda.

Ideia: cada mudança de estado é gravada num arquivo temporário e trocada de uma vez (os.replace). Se o processo
morre no meio, o arquivo da fila nunca fica pela metade e o lote recomeça de onde parou. Entre um item e outro há
uma espera aleatória, para não martelar o serviço do outro lado.

Garantia: nenhum item se perde. O item que estava em andamento na hora da queda pode ser refeito uma vez
(entrega "pelo menos uma vez"); por isso o trabalho de cada item deve aceitar repetição.
"""
import json
import os
import random
import sys
import tempfile
import time

PENDENTE, FEITO, FALHOU = "pendente", "feito", "falhou"


def gravar_atomico(caminho, dados):
    """Grava `dados` em JSON sem nunca deixar o arquivo pela metade."""
    pasta = os.path.dirname(os.path.abspath(caminho))
    fd, tmp = tempfile.mkstemp(dir=pasta, prefix=".fila-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)  # troca atômica no mesmo sistema de arquivos
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def criar(caminho, itens):
    gravar_atomico(caminho, {"itens": [{"id": i, "estado": PENDENTE, "tentativas": 0} for i in itens]})


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def processar(caminho, trabalho, espera=(0.0, 0.0), max_tentativas=3, dormir=time.sleep, sorteio=random.uniform):
    """Processa os itens pendentes, um por vez, gravando o estado depois de cada um.

    `trabalho(id)` faz o serviço e levanta exceção quando falha. Devolve um resumo com a contagem por estado.
    """
    fila = ler(caminho)
    primeiro = True
    for item in fila["itens"]:
        if item["estado"] != PENDENTE:
            continue
        if not primeiro:
            dormir(sorteio(*espera))
        primeiro = False
        try:
            trabalho(item["id"])
            item["estado"] = FEITO
        except Exception as erro:  # o lote continua; o item fica para a próxima rodada ou é dado como falho
            item["tentativas"] += 1
            item["erro"] = str(erro)[:200]
            if item["tentativas"] >= max_tentativas:
                item["estado"] = FALHOU
        gravar_atomico(caminho, fila)
    return {e: sum(1 for i in fila["itens"] if i["estado"] == e) for e in (PENDENTE, FEITO, FALHOU)}


if __name__ == "__main__":
    # Demonstração: `python fila.py fila.json registro.txt` anota cada item num registro e demora um pouco em cada um.
    arquivo, registro = sys.argv[1], sys.argv[2]

    def anotar(item):
        with open(registro, "a", encoding="utf-8") as f:
            f.write(f"{item}\n")
            f.flush()
            os.fsync(f.fileno())
        time.sleep(0.05)

    print(json.dumps(processar(arquivo, anotar)))
