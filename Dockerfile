FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY samples /app/samples
COPY prompts /app/prompts

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "postmortem_shield.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
