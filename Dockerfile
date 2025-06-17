FROM python:3.13-slim-bookworm

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install


CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]