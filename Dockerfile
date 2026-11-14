# Contêiner isolado do playbook: só Python e a biblioteca padrão. Os testes rodam sem rede e sem escrever fora de /tmp.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 lab
WORKDIR /playbook
COPY . .
USER lab
CMD ["python", "-m", "unittest", "-v"]
