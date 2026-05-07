FROM python:3.12-slim

WORKDIR /app

# Dependências do SO:
# - gcc, python3-dev, libpq-dev: para asyncpg (driver PostgreSQL)
# - libfreetype6-dev, libpng-dev, pkg-config: para matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

CMD ["python", "-m", "backend.main"]
