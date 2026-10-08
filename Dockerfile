FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DATABASE_PATH=/data/aion.db
WORKDIR /app
COPY app.py requirements.txt ./
COPY static ./static
RUN mkdir -p /data && useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app /data
USER appuser
EXPOSE 8000
CMD ["python", "app.py"]
