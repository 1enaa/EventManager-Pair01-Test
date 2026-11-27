FROM python:3.10-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# Create a non-root user with UID 1000
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 \
    --create-home --shell /usr/sbin/nologin appuser && \
    mkdir -p /app/data && \
    chown -R 1000:1000 /app/data

ENV PYTHONPATH=/code
ENV DATABASE_URL=sqlite:////app/data/events.db

WORKDIR /app

USER 1000:1000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/code", "--host", "0.0.0.0", "--port", "8000"]