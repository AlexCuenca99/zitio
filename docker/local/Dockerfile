FROM python:3.13-slim

ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install -r requirements-dev.txt && \
    rm -rf /root/.cache/pip

EXPOSE 8080

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "--threads", "4", "--timeout", "300", "src.main:app"]
