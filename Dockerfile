FROM python:3.10-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
ENV PYTHONPATH=/code
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "/code", "--host", "0.0.0.0", "--port", "8000"]
