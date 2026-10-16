FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY . .
COPY cloudflare/start.sh /usr/local/bin/etewitter-start
RUN chmod +x /usr/local/bin/etewitter-start && \
    mkdir -p /app/uploads /app/staticfiles && \
    python manage.py collectstatic --noinput

EXPOSE 8080
CMD ["/usr/local/bin/etewitter-start"]
