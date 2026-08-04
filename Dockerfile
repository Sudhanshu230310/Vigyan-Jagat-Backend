# --- Backend: FastAPI (Vigyan Jagat) ---
# Copy this file into the "Vigyan Jagat" project folder before building.

FROM python:3.12-slim

WORKDIR /app

# System deps needed by prisma-client-py to fetch its query engine binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate the Prisma client (needs schema.prisma present, which it is)
RUN prisma generate

# Cloud Run sets $PORT (defaults to 8080) — do not hardcode 8000/8080
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
