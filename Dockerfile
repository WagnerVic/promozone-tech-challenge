# Stage 1: builder — instala as dependências num venv isolado
FROM python:3.12-slim AS builder

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime — imagem final enxuta (sem ferramentas de build)
FROM python:3.12-slim

# Usuário não-root por segurança
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser
EXPOSE 8080

# Cloud Run injeta a variável PORT; escutamos nela (8080 como default local).
# 'exec' faz o uvicorn virar PID 1 e receber SIGTERM direto → shutdown gracioso.
CMD ["sh", "-c", "exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8080}"]
