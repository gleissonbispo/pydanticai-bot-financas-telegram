# Imagem base: Python 3.12 em versão slim (menor e mais segura)
FROM python:3.12-slim

# Define o diretório de trabalho dentro do container.
# Todos os comandos seguintes rodam a partir daqui.
WORKDIR /app

# Instala dependências do sistema operacional necessárias para:
# - asyncpg: precisa de libpq (driver PostgreSQL nativo)
# - compilação: gcc e python3-dev para pacotes que compilam código C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# O "rm -rf /var/lib/apt/lists/*" limpa o cache do apt para
# reduzir o tamanho da imagem final.

# Copia APENAS o requirements.txt primeiro.
# Por quê? Porque o Docker cacheia cada camada. Se o requirements.txt
# não mudou, o Docker reutiliza o cache do "pip install" (que é lento).
# Isso se chama "layer caching" e acelera muito os rebuilds.
COPY requirements.txt .

# Instala as dependências Python.
# --no-cache-dir: não guarda cache do pip (economia de espaço)
RUN pip install --no-cache-dir -r requirements.txt

# Agora copia todo o código da aplicação.
COPY backend/ ./backend/

# Comando que será executado quando o container iniciar.
CMD ["python", "-m", "backend.main"]