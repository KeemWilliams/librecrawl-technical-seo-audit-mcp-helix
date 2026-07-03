FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=5081 \
    REPORTS_DIR=/data/reports

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl fonts-dejavu libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /data/reports

EXPOSE 5081
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 5081), 3); s.close()"

CMD ["python", "server.py"]
