FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as an unprivileged user instead of root.
RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 5000
HEALTHCHECK CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:create_app()"]
