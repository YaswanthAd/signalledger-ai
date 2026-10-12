FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY signalledger/ ./signalledger/
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
USER app
ENV DB_PATH=/data/signalledger.db
EXPOSE 8011
CMD ["python", "-m", "uvicorn", "signalledger.api:app", "--host", "0.0.0.0", "--port", "8011"]
