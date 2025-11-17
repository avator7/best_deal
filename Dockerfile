FROM python:3.11-slim

# ----------------------------------------------------
# Install Chrome + dependencies
# ----------------------------------------------------
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver

# ----------------------------------------------------
# Set working directory
# ----------------------------------------------------
WORKDIR /app

# ----------------------------------------------------
# Copy and install Python dependencies
# ----------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------
# Copy project files
# ----------------------------------------------------
COPY . .

# ----------------------------------------------------
# Expose FastAPI port
# ----------------------------------------------------
EXPOSE 8000

# ----------------------------------------------------
# Run server (Cloud Run compatible)
# ----------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
