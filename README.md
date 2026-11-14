# lab-fila-atomica

**O que afirma:** uma fila de lote gravada com troca atômica não se corrompe nem perde item quando o processo morre no
meio. O lote recomeça de onde parou, e só o item que estava em andamento pode ser refeito.

De onde vem: um lote semanal de centenas de envios a um serviço web, que precisava aguentar queda do navegador e do
processo sem gastar crédito à toa. Aqui o "serviço" é só uma anotação num arquivo.

| Afirmação | Teste que prova |
|---|---|
| Queda seca (SIGKILL) não corrompe a fila nem perde item; no máximo um item é refeito | `test_queda_no_meio_nao_perde_item_nem_corrompe_a_fila` |
| Falha durante a gravação deixa a fila anterior intacta e não deixa arquivo temporário | `test_falha_durante_a_gravacao_deixa_a_fila_anterior_intacta` |
| Há espera aleatória entre itens, dentro da faixa pedida | `test_espera_aleatoria_entre_itens_dentro_da_faixa` |
| Item que falha é tentado até o limite e não trava o lote | `test_item_que_falha_e_tentado_ate_o_limite_e_nao_trava_o_lote` |

Limite: a entrega é "pelo menos uma vez". O trabalho de cada item precisa aceitar repetição.

## Como rodar

Precisa só de Docker.

```bash
./testar.sh
```

A imagem é construída aqui mesmo e os testes rodam com `--network none`, raiz somente leitura, sem privilégios e sem
pasta do hospedeiro montada. Só a biblioteca padrão do Python é usada, então nada é baixado além da imagem base.

## O que isto é, e o que não é

É um experimento do lab do [w3ss.tech](https://w3ss.tech) reescrito do zero para caber num contêiner. Não é cópia do que
roda no lab: não há nome de máquina, endereço, conta nem dado real. Os exemplos são inventados e os serviços de fora são
simulados dentro do contêiner.

A história completa está no post [Suno no piloto automático: 399 faixas, 91% de sucesso e por que o script venceu o agente](https://w3ss.tech/posts/suno-399-faixas-script-contra-agente/).

Outros experimentos: [lab-playbooks](https://github.com/W3SS/lab-playbooks).

## Licença

MIT. Veja [LICENSE](LICENSE).
