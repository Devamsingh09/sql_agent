# ── Base Image ────────────────────────────────────────
FROM python:3.11-slim

# ── Set working directory ──────────────────────────────
WORKDIR /app

# ── System dependencies ────────────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Copy requirements first (for Docker layer caching) ─
COPY requirements.txt .

# ── Install Python dependencies ────────────────────────
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy entire project ────────────────────────────────
COPY . .

# ── Create directory for SQLite database ──────────────
RUN mkdir -p /app/data

# ── Create Streamlit config ────────────────────────────
RUN mkdir -p /app/frontend/.streamlit
COPY frontend/.streamlit/secrets.toml /app/frontend/.streamlit/secrets.toml

# ── Supervisor config to run both services ─────────────
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── Expose ports ───────────────────────────────────────
# 8000 = FastAPI backend
# 8501 = Streamlit frontend
EXPOSE 8000 8501

# ── Start both services via supervisor ─────────────────
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]