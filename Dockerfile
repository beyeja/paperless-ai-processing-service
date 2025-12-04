# Dockerfile for webhook_service
FROM python:3.13-slim

WORKDIR /usr/src/app

# Copy requirements file and install dependencies
COPY requirements.txt .
# Copy the rest of the application code into the container
COPY . .

# Install any necessary system dependencies
RUN pip install --no-cache-dir -r requirements.txt

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c 'import urllib.request; urllib.request.urlopen("http://localhost:5000/health", timeout=1)' && exit 0 || exit 1

# Expose the port the app will run on
EXPOSE 5000

# The script files will be mounted at runtime.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "1", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "server:app"]