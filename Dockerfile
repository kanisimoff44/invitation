FROM python:3.12-slim

# Не писать .pyc, не буферизовать stdout (логи сразу видны в docker logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Зависимости отдельным слоем — кешируются, пока не меняется requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения.
COPY app ./app

# Непривилегированный пользователь по умолчанию (uid 1000). Реальный uid/gid
# процесса можно переопределить в docker-compose (user:), чтобы он совпал с
# владельцем смонтированного каталога data/ на сервере.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
