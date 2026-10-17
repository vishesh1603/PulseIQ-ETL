FROM apache/superset:3.1.3

USER root
# Install psycopg2-binary so Superset can query PostgreSQL warehouse
RUN pip install --no-cache-dir psycopg2-binary

# Superset configuration and bootstrap script
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
COPY superset_config.py /app/superset_config.py
COPY docker-init.sh /app/docker-init.sh
RUN chmod +x /app/docker-init.sh

USER superset
WORKDIR /app

ENTRYPOINT ["/app/docker-init.sh"]
