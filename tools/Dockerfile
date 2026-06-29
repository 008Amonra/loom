FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY tools-server.py .

RUN pip install --no-cache-dir flask pillow

RUN useradd -m tools && chown -R tools:tools /app
USER tools

EXPOSE 5006
CMD ["python3", "tools-server.py", "5006"]