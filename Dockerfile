FROM python:3.11-slim-bullseye AS builder
WORKDIR /app
COPY ./pyproject.toml /app
RUN pip install uv && uv sync

FROM python:3.11-slim-bullseye
EXPOSE 8080
COPY --from=builder /app/.venv/lib/python3.11/site-packages /app/.venv/lib/python3.11/site-packages
WORKDIR /app
COPY ./setup.sh /app
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* /tmp/* \
    && chmod +x /app/setup.sh
ENTRYPOINT ["/app/setup.sh"]