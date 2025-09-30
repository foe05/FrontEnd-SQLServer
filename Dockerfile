# Multi-stage build for optimized Docker image
FROM python:3.11-slim AS builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server (runtime)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r streamlit && useradd -r -g streamlit streamlit

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=streamlit:streamlit . /app/

# Create directories with proper permissions (as root before switching user)
RUN mkdir -p /app/cache /app/logs /home/streamlit/.streamlit \
    && chown -R streamlit:streamlit /app/cache /app/logs /home/streamlit

# Create Streamlit configuration (as root)
RUN echo '[server]\n\
port = 8501\n\
address = "0.0.0.0"\n\
headless = true\n\
enableCORS = true\n\
enableXsrfProtection = false\n\
allowRunOnSave = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[global]\n\
embedOptions = ["frameless"]\n\
\n\
[theme]\n\
base = "light"\n\
primaryColor = "#0066cc"\n\
backgroundColor = "#ffffff"\n\
secondaryBackgroundColor = "#f0f2f6"\n\
textColor = "#262730"' > /home/streamlit/.streamlit/config.toml \
    && chown -R streamlit:streamlit /home/streamlit/.streamlit

# Switch to non-root user
USER streamlit

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py"]
