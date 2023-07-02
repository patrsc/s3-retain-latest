FROM python:3.11.4-alpine3.18

RUN pip install poetry
WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

COPY main.py .

CMD ["poetry", "run", "python", "main.py"]
