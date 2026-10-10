FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Fonts for Pillow image rendering.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Handles Windows CRLF line endings.
RUN sed -i 's/\r$//' /app/entrypoint.sh

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]