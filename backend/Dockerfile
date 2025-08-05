FROM python:3.11-slim

WORKDIR /app/

COPY pyproject.toml poetry.lock /app/

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main

COPY app /app/app
COPY insurance-sample.pdf /app/app/insurance-sample.pdf


#COPY .env /app/app/
#CMD ["sleep","infinity"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
