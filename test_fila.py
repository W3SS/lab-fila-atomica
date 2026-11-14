import collections
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import fila

AQUI = os.path.dirname(os.path.abspath(__file__))


class FilaAtomica(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.arquivo = os.path.join(self.pasta, "fila.json")
        self.registro = os.path.join(self.pasta, "registro.txt")

    def test_queda_no_meio_nao_perde_item_nem_corrompe_a_fila(self):
        itens = [f"item-{n:02d}" for n in range(40)]
        fila.criar(self.arquivo, itens)
        proc = subprocess.Popen([sys.executable, os.path.join(AQUI, "fila.py"), self.arquivo, self.registro])
        limite = time.time() + 20
        while time.time() < limite:  # espera o lote andar um pouco
            if os.path.exists(self.registro) and sum(1 for _ in open(self.registro)) >= 8:
                break
            time.sleep(0.01)
        proc.send_signal(signal.SIGKILL)  # queda seca: sem chance de limpar nada
        proc.wait()

        estado = fila.ler(self.arquivo)  # o arquivo continua sendo JSON válido
        feitos = sum(1 for i in estado["itens"] if i["estado"] == fila.FEITO)
        self.assertGreaterEqual(feitos, 1)
        self.assertLess(feitos, len(itens), "a queda precisa acontecer antes do fim para o teste valer")

        subprocess.run([sys.executable, os.path.join(AQUI, "fila.py"), self.arquivo, self.registro], check=True)
        final = fila.ler(self.arquivo)
        self.assertTrue(all(i["estado"] == fila.FEITO for i in final["itens"]))

        vezes = collections.Counter(linha.strip() for linha in open(self.registro))
        self.assertEqual(set(vezes), set(itens), "nenhum item se perdeu")
        repetidos = [i for i, n in vezes.items() if n > 1]
        self.assertLessEqual(len(repetidos), 1, "só o item em andamento na queda pode ser refeito")
        self.assertTrue(all(n <= 2 for n in vezes.values()))

    def test_falha_durante_a_gravacao_deixa_a_fila_anterior_intacta(self):
        fila.criar(self.arquivo, ["a", "b"])
        antes = open(self.arquivo, encoding="utf-8").read()
        with mock.patch("os.replace", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                fila.gravar_atomico(self.arquivo, {"itens": []})
        self.assertEqual(open(self.arquivo, encoding="utf-8").read(), antes)
        self.assertEqual([n for n in os.listdir(self.pasta) if n.endswith(".tmp")], [], "não sobra arquivo temporário")

    def test_espera_aleatoria_entre_itens_dentro_da_faixa(self):
        fila.criar(self.arquivo, ["a", "b", "c", "d"])
        esperas = []
        fila.processar(self.arquivo, lambda _i: None, espera=(20, 90), dormir=esperas.append)
        self.assertEqual(len(esperas), 3, "não espera antes do primeiro item")
        self.assertTrue(all(20 <= s <= 90 for s in esperas))

    def test_item_que_falha_e_tentado_ate_o_limite_e_nao_trava_o_lote(self):
        fila.criar(self.arquivo, ["bom", "ruim"])

        def trabalho(item):
            if item == "ruim":
                raise RuntimeError("aviso do serviço antes de criar")

        for _ in range(3):
            resumo = fila.processar(self.arquivo, trabalho, max_tentativas=3)
        self.assertEqual(resumo, {fila.PENDENTE: 0, fila.FEITO: 1, fila.FALHOU: 1})
        ruim = [i for i in fila.ler(self.arquivo)["itens"] if i["id"] == "ruim"][0]
        self.assertEqual(ruim["tentativas"], 3)
        self.assertIn("aviso do serviço", ruim["erro"])


if __name__ == "__main__":
    unittest.main()
