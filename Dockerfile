FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --requirement requirements.txt \
    && pip uninstall --yes pip setuptools wheel

COPY . .
RUN chmod 0755 docker-entrypoint.sh \
    && mkdir -p /app/static /app/media \
    && chown -R 10001:10001 /app/static /app/media

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent -H "Host: ${HEALTHCHECK_HOST:-localhost}" http://127.0.0.1:8000/healthz/ >/dev/null || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "CORE.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
