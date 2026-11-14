#!/usr/bin/env bash
# Constrói a imagem e roda os testes num contêiner isolado: sem rede, raiz somente leitura, sem privilégios e sem
# nenhuma pasta do hospedeiro montada. Só /tmp é gravável, e some quando o contêiner termina.
set -euo pipefail
cd "$(dirname "$0")"
docker build --quiet --tag lab-fila-atomica . >/dev/null
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=64m \
  --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 --memory 256m lab-fila-atomica
